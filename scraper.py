import re
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
from collections import defaultdict
import pickle

largest_page = 0 # Store largest page length - factoring in filters for stopwords, numbers, and punctuation

def scraper(url, resp):
    global largest_page
    if resp.status != 200 or len(resp.raw_response.content) == 0: # If request is unsuccessful - not an OK response - or page has no content, then return an empty URL list
        return []
    
    soup = BeautifulSoup(resp.raw_response.content, 'lxml') # Parse html with lxml parser
    text = soup.get_text()
    stopWords = set(stopwords.words('english')) # Load in stopwords list from NLTK
    
    tokenizer = RegexpTokenizer(r'\w+') # Use regex tokenizer to grab only words
    tokens = tokenizer.tokenize(text)
    
    wordsFiltered = []
    tokensFiltered = []
    
    for token in tokens:
        if token.isalpha(): # Filter out number tokens
            tokensFiltered.append(token.lower()) # Convert tokens to lowercase to prevent dupes
    for token in tokensFiltered: # Finally, filter all stopwords out
        if token not in stopWords:
            wordsFiltered.append(token)
            
    if len(tokensFiltered) < 50: # Filter out low-content pages
        return []
    

    subdomains_dict = defaultdict(int) # Prepare dictionary to store subdomains and the number of unique pages within them (ics.uci.edu domain)
    with open('subdomains.pickle', 'rb') as f:
        subdomains_dict = pickle.load(f)
        
    parsed = urlparse(url)
    if re.match(r'(.*[^www].+\.ics\.uci\.edu)', parsed.netloc): # If the domain is detected to be ics.uci.edu:
        subdomains_dict["https://" + parsed.netloc] += 1        #       add it to the dictionary
        
    with open('subdomains.pickle', 'wb') as f:
        pickle.dump(subdomains_dict, f, protocol=pickle.HIGHEST_PROTOCOL)
    

    common_words_dict = defaultdict(int) # Prepare dictionary to store word frequency
    with open('common_words.pickle', 'rb') as f:
        common_words_dict = pickle.load(f)
        
    for word in wordsFiltered:
        common_words_dict[word] += 1 # Add each word found after filtering to the dictionary
        
    with open('common_words.pickle', 'wb') as f:
        pickle.dump(common_words_dict, f, protocol=pickle.HIGHEST_PROTOCOL)
        
            
    if len(tokensFiltered) > largest_page: # Update largest page count if global variable is exceeded
        with open('largest_page.txt', 'w') as f:
            largest_page = len(tokensFiltered)
            f.write(str(largest_page))
            f.write(url)
        
    
    links = extract_next_links(url, resp) # Collect all links from page
    return [link for link in links if is_valid(link)] # Return collected links if valid


def extract_next_links(url, resp):
    list_of_links = []
    
    if resp.status == 200: # If response is OK:
        if len(resp.raw_response.content) < 5000000: # Filter out extremely large pages
            soup = BeautifulSoup(resp.raw_response.content, 'lxml')
            text = soup.get_text()
                        
            for link in soup.find_all('a'):
                list_of_links.append(link.get('href')) # Add extracted links to the list to return
    else:
        print(resp.error)

    return list_of_links


def is_valid(url):
    try:
        parsed = urlparse(url) # Parse URLs into segments

        if parsed.scheme not in set(["http", "https"]):
            return False 
        
        today_check = parsed.netloc + parsed.path # Combine netloc and path specifically for today.uci.edu.***
        # Filter out any URLs that do not match provided domains
        if not re.match(r"(.+\.ics\.uci\.edu$)|(.*\.cs\.uci\.edu$)|(.+\.informatics\.uci\.edu$)|(.+\.stat\.uci\.edu$)", parsed.netloc) and not(re.match(r"^today\.uci\.edu\/department\/information_computer_sciences$", today_check) or re.match(r"today\.uci\.edu\/department\/information_computer_sciences\/.+$", today_check)):
            return False
        
        # Ignore URLs with fragments
        if len(parsed.fragment) > 0:
            return False
        
        # Filter out evoke pages due to low content
        if re.search(r"evoke.ics.uci.edu", url):
            return False
        # Filter out calendars/events
        if re.search(r"wics.ics.uci.edu/events", url):
            return False
        # Filter out URLs for social media share buttons
        if re.search(r"share=", parsed.query):
            return False
        # Filter out URLs for file download prompts
        if re.search(r"download=", parsed.query):
            return False
        # Filter out URLs for replies to comments
        if re.search(r"(replytocom)", parsed.query):
            return False
        # Filter out URLs with file extensions
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|ppsx|txt)$", parsed.path.lower()):
            return False
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|ppsx|txt)$", parsed.query.lower()):
            return False
        
        # load pickle file in
        url_dict = defaultdict(int)
     
        with open('unique_pages.pickle', 'rb') as f:
            url_dict = pickle.load(f)

        # do something with pickle data
        url_dict[url] = 1 # Add page to dictionary if unique

        # update pickle file
        with open('unique_pages.pickle', 'wb') as f:
            pickle.dump(url_dict, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise
        
       