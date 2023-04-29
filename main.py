from datetime import datetime
import logging

# nlp tookit thingy
import nltk


from nltk.stem import WordNetLemmatizer

import numpy as np
import os 
import re
import sys
import time
from tkinter import *
from tkinter import filedialog


WLIST_PATH = "allow.wlist"
TITLE = "Just A Normal Text Editor"
MESSAGE = "Your text was deleted due to spelling error(s).\nThe word(s) \"[word]\" are not recognized.\nIf you think this was a mistake, please add the word to the whitelist with Ctrl+M.\n\nThis action is irreversible."

def log_setup(logger_file, format='%(name)s - %(levelname)s - %(message)s'):
    logging.basicConfig(filename=logger_file, filemode='w', format=format)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    return logger 

def nltk_setup():
    # add the path to the NLTK data directory
    nltk_data_dir = 'nltk_data'
    nltk.data.path.append(os.path.join(os.getcwd(), nltk_data_dir))

    nltk.download('words')
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('wordnet')
    nltk.download('omw-1.4')

    lemmatizer = WordNetLemmatizer()

    # Define a vectorized function to lemmatize the words and apply the correct POS tag
    v_lemmatize = np.vectorize(lambda word: lemmatizer.lemmatize(word, get_wordnet_pos(word)))

    return v_lemmatize

# Define a function to get the appropriate part of speech for each word
def get_wordnet_pos(word):
    # Map POS tag to first character used by WordNetLemmatizer
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": nltk.corpus.wordnet.ADJ,
                "N": nltk.corpus.wordnet.NOUN,
                "V": nltk.corpus.wordnet.VERB,
                "R": nltk.corpus.wordnet.ADV}
    return tag_dict.get(tag, nltk.corpus.wordnet.NOUN)

class CheckTrigger:
    def __init__(self, char):
        self.char = char


class Editor:
    def __init__(self, v_lemmatize, troll_mode=False):

        self.troll_mode = troll_mode 
        print(troll_mode)
        
        self.test_content = 'The quick brown fox jumps over the lazy dog.'
        self.aggsc = troll_mode == True
        self.aggsc_setup()
        self.cache_word = None
        self.v_lemmatize = v_lemmatize
        self.init_checked = 0
        self.enabled_display = 'Idle' if troll_mode == False else 'deal with it'

        self.mode = 1
        self.file_path = ''

        self.master = Tk()
        self.master.attributes("-topmost", True)
        self.master.iconbitmap('icon.ico')

        # Title
        self.file_name = 'Untitled'
        self.update_title(text=self.file_name)

        # Text widget
        self.text_area = Text(self.master)
        self.text_area.pack(fill=BOTH, expand=True)
        self.text_area.bind('<Key>', self.on_content_update)

        # Footer
        self.footer_frame = Frame(self.master)
        self.footer_frame.pack(side=BOTTOM, fill=X, anchor=SE)

        self.footer_doc_status = Label(self.footer_frame, text=TITLE)
        self.footer_doc_status.pack(side=LEFT)

        self.footer_aggsc_info = Label(self.footer_frame, text=f"AggSC: {self.enabled_display if self.aggsc else 'OFF'}")
        self.footer_aggsc_info.pack(side=RIGHT)

        


        # Header (Menus)
        menu = Menu(self.master)
        file_menu = Menu(menu, tearoff=0)
        mode_menu = Menu(menu, tearoff=0)

        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.save_file_as, accelerator="Ctrl+Shift+S")
        
        mode_menu.add_command(label="Toggle Theme", command=self.toggle_mode)

        menu.add_cascade(label="File", menu=file_menu)
        menu.add_cascade(label="Mode", menu=mode_menu)

        self.master.config(menu=menu)

        # Keyboard Shortcut Binds
        self.master.bind('<Control-n>', self.new_file)
        self.master.bind('<Control-o>', self.open_file)
        self.master.bind('<Control-s>', self.save_file)
        self.master.bind('<Control-S>', self.save_file_as)
        self.master.bind('<Control-e>', self.aggsc_toggle)
        self.master.bind('<Control-m>', self.whitelist_word)

        self.master.mainloop()
        
    def toggle_mode(self, event=None):
        self.mode = not(self.mode)
        temp = self.text_area.get(1.0, END)
        
        # I will just leave the color configs as is
        if self.mode: 
            bg = "white"
            fg = "black"
        else:
            bg = "black"
            fg = "white"

        self.text_area.destroy()

        self.text_area = Text(self.master, bg=bg, fg=fg)
        self.text_area.pack(fill=BOTH, expand=True)
        self.text_area.bind('<Key>', self.on_content_update)
        self.text_area.insert(END, temp)


    def aggsc_toggle(self, event=None):
        if self.troll_mode:
            self.aggsc = True
        else:
            self.aggsc = not(self.aggsc)
        self.footer_aggsc_info.config(text=f"AggSC: {self.enabled_display if self.aggsc else 'OFF'}")
        if self.init_checked == 0 and self.aggsc:
            event = CheckTrigger(' ')
            self.on_content_update(event=event)

            self.init_checked = 1

    def aggsc_setup(self):
        self.english_words = np.array(list(set(nltk.corpus.words.words())))
        with open(WLIST_PATH, 'r') as f:
            self.allow_list = np.array([word.lower() for word in f.read().splitlines()])

        if self.troll_mode: 
            self.allow_list = np.array([])

    def whitelist_word(self, event=None):
        if self.cache_word != None:
            with open(WLIST_PATH, 'a') as f:
                f.write(f'{self.cache_word}\n')

            if not self.troll_mode:
                self.allow_list = np.append(self.allow_list, self.cache_word)
            
            self.cache_word = None
            self.text_area.insert(END, "Word successfully added")

    def on_content_update(self, event=None):
        self.update_title(text=f"{self.file_name}*")

        if event.char == ' ' and self.aggsc: 
            self.footer_aggsc_info.config(text=f"AggSC: Checking")

            t1 = time.perf_counter()

            # aggressive spell check
            """
            1. get contents
            2. strip of newlines and whitespaces
            3. remove punctuation
            4. lowercase letters
            5. split into words by space
            6. convert to np array
            7. apply lemmatization
            """

            sc_content = self.text_area.get(1.0, END) 

            if sc_content.isspace(): 
                sc_content = self.test_content

            sc_content = sc_content.strip()
            sc_content = re.sub(r'[^\w\s]', '', sc_content)
            sc_content = sc_content.lower()
            sc_content = sc_content.split()
            sc_content = np.array(sc_content)
            sc_content = np.vectorize(lambda x: x if not np.char.isdigit(x) else "")(sc_content)
            sc_content = sc_content[sc_content != ""]
            sc_content = self.v_lemmatize(sc_content)

            valid_words = np.logical_or(np.isin(sc_content, self.english_words), 
                                        np.isin(sc_content, self.allow_list))
            if not np.all(valid_words):
                invalid_words = sc_content[~valid_words]
                self.text_area.delete(1.0, END)
                self.text_area.insert(END, MESSAGE.replace('[word]', invalid_words[0]))

                if self.file_path != None and self.file_path != '':
                    with open(self.file_path, 'w') as file:
                        file.write('')

                    self.updater()
                    self.update_footer(text=f"Saved {self.file_path}")
                
                self.cache_word = invalid_words[0]
            
            print(f'{(time.perf_counter() - t1):.4f}')

            self.footer_aggsc_info.config(text=f"AggSC: {self.enabled_display}")
            

    def updater(self):
        self.cache_word = None

        self.text_area.bind('<Key>', self.on_content_update)
        self.file_name = os.path.basename(self.file_path)
        if self.file_name == '':
            self.file_name = 'Untitled'
        self.update_title(text=self.file_name)

    def update_title(self, text):
        self.master.title(f"{text} - {TITLE}")

    def update_footer(self, text):
        self.footer_doc_status.config(text=f"{text} ({self.get_timestamp()})")

    def get_timestamp(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        return current_time

    # File op

    def new_file(self, event=None):
        self.text_area.delete(1.0, END)
        self.file_path = ''
        self.updater()
        self.update_footer(text=f"Created new file")

    def open_file(self, event=None):
        temp = self.file_path

        self.file_path = filedialog.askopenfilename()
        if self.file_path:
            with open(self.file_path, 'r') as file:
                self.text_area.delete(1.0, END)
                self.text_area.insert(END, file.read())

            self.updater()
            self.update_footer(text=f"Opened {self.file_path}")

        else:
            self.file_path = temp
            print('No file selected.')



    def save_file(self, event=None):
        if self.file_path != None and self.file_path != '':
            with open(self.file_path, 'w') as file:
                file.write(self.text_area.get(1.0, END))

            self.updater()
            self.update_footer(text=f"Saved {self.file_path}")

        else:
            self.save_file_as()


    def save_file_as(self, event=None):
        temp = self.file_path
        self.file_path = filedialog.asksaveasfilename(defaultextension=".txt")
        
        if self.file_path:
            with open(self.file_path, 'w') as file:
                file.write(self.text_area.get(1.0, END))

            self.updater()
            self.update_footer(text=f"Saved as {self.file_path}")

        else:
            self.file_path = temp
            print('No save path selected.')



def main():
    log_setup('debug.log')

    v_lemmatize = nltk_setup()
    Editor(v_lemmatize, troll_mode=False)

if __name__ == '__main__':
    main()