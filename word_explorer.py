import requests
from bs4 import BeautifulSoup
import time
import random
import queue
import os

GLOBAL_A = set()
GLOBAL_B = set()


class RecursiveSynonymFinder:
    def __init__(self, word_class: str, start_word: str = None):

        self.__word_class = word_class

        self.__search_url = 'https://www.synonymordboka.no/no/'
        self.__dictionary_lookup_url = 'https://www.naob.no/ordbok/'
        self.__dictionary_search_url = 'https://www.naob.no/søk/'
        self.__title_suffix = 'synonym of '

        self.__output_root_folder = f'output/{word_class}/'
        self.__create_folder_if_absent(self.__output_root_folder)

        self.__word_class_matches_file = self.__output_root_folder + 'matches.txt'
        self.__expanded_matches_file = self.__output_root_folder + 'expanded_matches.txt'
        self.__negative_matches_file = self.__output_root_folder + 'words_not_of_class.txt'

        temp_matches = self.__get_matches_from_file()
        temp_neg_matches = self._get_negative_matches_from_file()
        temp_exp_matches = self.__get_expanded_matches_file()

        self.__matches: set = temp_matches if temp_matches else set()
        if start_word:
            self.__matches.add(start_word)
        self.__negative_matches: set = temp_neg_matches if temp_neg_matches else set()
        self.__expanded_matches: set = temp_exp_matches if temp_exp_matches else set()

        print('init matches', self.__matches)
        self.__word_queue: queue.Queue = queue.Queue()
        [self.__word_queue.put(i) for i in self.__matches if i not in self.__expanded_matches]

        self.__sleep_time = 0
        self.__last_write_time = time.time()
        self.__write_interval = 120
        self.__max_recursion_depth = 50
        self.__delay_interval_search = (0, 1.0)
        self.__delay_interval_lookup = (0, 0.1)
        self.__delay_on_error = 5
        self.__lookup_max_tries = 5
        self.__session = requests.Session()

    def do_search(self):
        start_time = time.time()
        while True:
            word = self.__word_queue.get()
            print(f'---')
            print(f'[STATUS] Looking for <{self.__word_class}>')
            print(f'[STATUS] Matches found:             {len(self.__matches)}')
            print(f'[STATUS] Matches expanded:          {len(self.__expanded_matches)}')
            print(f'[STATUS] Words not of class found:  {len(self.__negative_matches)}')
            print(f'[STATUS] Approx queue size:         {self.__word_queue.qsize()}')
            print(f'[STATUS] Time used (s):             {time.time() - start_time} ({self.__sleep_time}s sleep time)')
            print(f'---')

            if word:
                print(f'[New word] {word}')
                adj_candidates = {
                    synonym for synonym in self.search_for_synonyms(word)
                    if synonym not in self.__matches and len(synonym.split(' ')) == 1
                }

                new_matches = self.verify_word_classes(adj_candidates, create_new_session=True)

                for match in new_matches:
                    self.__word_queue.put(match)
                    self.__matches.add(match)
                self.__expanded_matches.add(word)

                difference = self.__expanded_matches.difference(self.__matches)
                if difference:
                    print(f'THESE WORDS ARE NOT {self.__word_class.upper()}!!!')
                    print(difference)
                    GLOBAL_A.update(difference)
                    GLOBAL_B.update(self.__matches.copy())
                    break

                # write to file if enough time has gone by
                if (time.time() - self.__last_write_time) > self.__write_interval:
                    self.__write_data_to_files()
                    self.__last_write_time = time.time()

    def verify_word_classes(self, match_candidates: set, word_class: str = None, create_new_session: bool = False) -> set:
        if not word_class:
            word_class = self.__word_class

        print(f'[Verify word classes] {len(match_candidates)} valid candidates.')
        approved_matches = set()
        accumulated_wait_time = 0.0
        lookup_start_time = time.time()

        session = requests.session() if create_new_session else self.__session

        for candidate in match_candidates:
            # print('Candidate', candidate)
            if candidate not in self.__negative_matches:
                wait_time = self.__get_random_wait_time(self.__delay_interval_lookup)
                time.sleep(wait_time)
                accumulated_wait_time += wait_time
                lookup_result = self.lookup_word(candidate, word_class)
                if lookup_result:
                    approved_matches.add(candidate)
                else:
                    self.__negative_matches.add(candidate)

        if create_new_session:
            session.close()
        self.__sleep_time += accumulated_wait_time
        print(f'[Lookup <{self.__word_class}>] {len(approved_matches)} approved in {time.time() - lookup_start_time} seconds.')
        return approved_matches

    def lookup_word(self, word: str, word_class: str = None, session: requests.Session = None):
        if not word_class:
            word_class = self.__word_class

        if not session:
            session = self.__session

        word_dictionary_lookup_url = self.__dictionary_lookup_url + word
        word_search_url = self.__dictionary_search_url + word

        for it in range(self.__lookup_max_tries):
            try:
                candidate_result = session.get(word_dictionary_lookup_url)
                candidate_doc = BeautifulSoup(candidate_result.text, 'html5lib')

                # is this a main page?
                word_class_result = candidate_doc.find('div', {'class': 'ordklasseledd'})
                if word_class_result and RecursiveSynonymFinder.is_equal(word_class_result.text, word_class):
                    return True
                else:
                    # Try to use the search to find a match
                    search_result = session.get(word_search_url)
                    search_doc = BeautifulSoup(search_result.text, 'html5lib')
                    search_hits = search_doc.find_all('div', {'class': 'list-item'})

                    for hit in search_hits:
                        hit_value = hit.find('a', {'class': 'article-headword'})
                        hit_class = hit.find('span', {'class': 'ordklasse-shortform'})
                        if hit_value and RecursiveSynonymFinder.is_equal(hit_value.text, word):
                            if hit_class and RecursiveSynonymFinder.is_equal(hit_class.text, word_class):
                                return True
                    return False
            except Exception as e:
                print(f'[lookup_word] ERROR ({word}):', e)
                time.sleep(self.__delay_on_error)
                self.__sleep_time += self.__delay_on_error

    def search_for_synonyms(self, word: str) -> set:
        wait_time = self.__get_random_wait_time(self.__delay_interval_search)
        time.sleep(wait_time)
        self.__sleep_time += wait_time
        for i in range(self.__lookup_max_tries):
            try:
                # print(f'[depth={depth}][{word.capitalize()}] Waited {wait_time}s before searching.')
                result = self.__session.get(self.__search_url, params={'q': word})
                doc: BeautifulSoup = BeautifulSoup(result.text, 'html5lib')
                sub_search = self.__title_suffix + word
                synonyms = doc.find_all('a', {'title': sub_search})
                print(f'[Synonym search] Found {len(synonyms)} synonyms for the word "{word}".')
                return {i.text for i in synonyms}
            except Exception as e:
                print(f'[search_for_synonyms] ERROR ({word}):', e)
                time.sleep(self.__delay_on_error)
                self.__sleep_time += self.__delay_on_error
        return set()



    @staticmethod
    def __get_params(url: str):
        return {i.split('=')[0]: i.split('=')[1] for i in url.split('?')[-1].split('&')}

    @staticmethod
    def __get_random_wait_time(interval: tuple):
        return random.random() * (interval[1] - interval[0]) + interval[0]

    def __write_data_to_files(self):
        print('[I/O] Writing resources to files')
        self.__write_to_matches_file()
        self.__write_to_expanded_matches_file()
        self.__write_to_negative_matches_file()

    def __get_matches_from_file(self) -> set:
        return self.__file_interaction(self.__word_class_matches_file)

    def __write_to_matches_file(self) -> None:
        self.__file_interaction(self.__word_class_matches_file, self.__matches, 'w')

    def _get_negative_matches_from_file(self) -> set:
        return self.__file_interaction(self.__negative_matches_file)

    def __write_to_negative_matches_file(self) -> None:
        self.__file_interaction(self.__negative_matches_file, self.__negative_matches, 'w')

    def __get_expanded_matches_file(self) -> set:
        return self.__file_interaction(self.__expanded_matches_file)

    def __write_to_expanded_matches_file(self) -> None:
        self.__file_interaction(self.__expanded_matches_file, self.__expanded_matches, 'w')

    @staticmethod
    def __file_interaction(file: str, data: set = None, mode: str = 'r') -> set:
        try:
            if mode == 'w':
                with open(file, 'w', encoding='utf-8') as f:
                    for i in data:
                        f.write(i + '\n')
            else:
                with open(file, 'r', encoding='utf-8') as f:
                    return {i.strip('\n') for i in f.readlines()}
        except FileNotFoundError as e:
            print(e)

    @staticmethod
    def is_equal(a: str, b: str):
        return a.lower().strip() == b.lower().strip()

    @staticmethod
    def __create_folder_if_absent(directory: str) -> None:
        os.makedirs(directory, exist_ok=True)


if __name__ == '__main__':
    test = RecursiveSynonymFinder('substantiv', 'bil')
    test.do_search()
