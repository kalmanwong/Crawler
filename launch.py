from configparser import ConfigParser
from argparse import ArgumentParser

from utils.server_registration import get_cache_server
from utils.config import Config
from crawler import Crawler
from collections import defaultdict
import pickle


def main(config_file, restart):
    cparser = ConfigParser()
    cparser.read(config_file)
    config = Config(cparser)
    config.cache_server = get_cache_server(config, restart)
    
    # Initialize empty pickles to store data for report
    
    empty_dict = defaultdict(int)
    with open('unique_pages.pickle', 'wb') as f:
        pickle.dump(empty_dict, f, protocol=pickle.HIGHEST_PROTOCOL)
        
    empty_dict2 = defaultdict(int)
    with open('common_words.pickle', 'wb') as f:
        pickle.dump(empty_dict2, f, protocol=pickle.HIGHEST_PROTOCOL)
        
    empty_dict3 = defaultdict(int)
    with open('subdomains.pickle', 'wb') as f:
        pickle.dump(empty_dict3, f, protocol=pickle.HIGHEST_PROTOCOL)
    
    
    crawler = Crawler(config, restart)
    crawler.start()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--restart", action="store_true", default=False)
    parser.add_argument("--config_file", type=str, default="config.ini")
    args = parser.parse_args()
    main(args.config_file, args.restart)
