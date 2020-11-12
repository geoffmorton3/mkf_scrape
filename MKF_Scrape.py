from selenium import webdriver
import time
import pandas as pd
import time
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
import re


def run_scrape(url):
    results = []
    
    driver = webdriver.Chrome(executable_path = 'C:/Users/geoff/Downloads/chromedriver_win32/chromedriver.exe')
    driver.get(url)
    
    # From the main NFL page, click on the game
    # The 2nd last div[x] element should cycle through the games
    for i in range(1,20,4):
        for ii in range (0,4):
            try:
                driver.get(url)
                time.sleep(2)
                n = i+ii
                game_path = "//*[@id='root']/div/main/div[1]/div/div[2]/div/div[4]/div[2]/div[%d]" % (n)
                print(game_path)
                driver.find_element_by_xpath(game_path).click()
                time.sleep(1)
            except NoSuchElementException:
                break
            
            try:
                promo_path = '//*[@id="container"]/div[2]/div/div/div/div[1]/div[2]/button'
                driver.find_element_by_xpath(promo_path).click()
            except NoSuchElementException:
                print("No Promo")
            
            # From the game page, click on the game type, then select More or Less games
            try:
                list_path = '//*[@id="root"]/div/main/div[1]/div/div[2]/div/div[2]/div/div/div/div'
                driver.find_element_by_xpath(list_path).click()
                time.sleep(1)
            except ElementClickInterceptedException:
                print("Issue with Game " + str(i))
                continue
            
            try:
                moreorless_path = '//*[@id="menu-game"]/div[2]/ul/li[3]'
                driver.find_element_by_xpath(moreorless_path).click()
                time.sleep(1)
            except ElementClickInterceptedException:
                print("Issue with Game " + str(i))
                continue
            
            # From the more or less page, click on the game and cycle through all games
            for j in range(1,20):
                try:
                    contest_path = '//*[@id="priceList"]/div[%d]' % (j)
                    driver.find_element_by_xpath(contest_path).click()
                    time.sleep(1)
                except NoSuchElementException:
                    break
            
                # This works for More or Less contests that are not for fantasy points
                for k in range(1,10):
                    path_player = "//*[@id='root']/div/main/div[1]/div/div[2]/div/div[7]/div[%d]/div/h3[1]" % (k)
                    path_stats = "//*[@id='root']/div/main/div[1]/div/div[2]/div/div[7]/div[%d]/div/h3[2]" % (k)
                    try:
                        player_elem = driver.find_element_by_xpath(path_player)
                        player = player_elem.get_attribute('innerHTML')
                        stats_elem = driver.find_element_by_xpath(path_stats)
                        stats = stats_elem.get_attribute('innerHTML')
                        #print(player_elem.get_attribute('innerHTML'))
                        #print(stats_elem.get_attribute('innerHTML'))
                    except NoSuchElementException:
                        break
                    
                    results.append([n,j,k,player,stats])
                
    
    df = pd.DataFrame(results, columns=['game','contest','player_num','player_name','stat_string'])
    df['stat_val'] = df['stat_string']
    df['stat_name'] = df['stat_string']
    
    for i in range(0,len(df)):
        text = df.iloc[i,4]
        left = '<span style="font-size: 20px;">'
        right = '</span><br>'
        text_new = text[text.index(left)+len(left):text.index(right)]
        df.at[i,'stat_val'] = text_new
        
        text = df.iloc[i,4]
        left = '</span><br>'
        text_new = text[text.index(left)+len(left):]
        if "Fantasy" in text_new:
            text_new = 'Fantasy Points'
        df.at[i,'stat_name'] = text_new
    
    df = df.drop('stat_string',axis=1)
    
    return df

    
def merge_rankings(mkf_df,rank_file):
    rank_df = pd.read_csv(rank_file)
    df = pd.merge(left=mkf_df,right=rank_df,how='left',left_on='player_name',right_on='Player')
    
    return df

def clean_rankings(df):
    for i in range(0,len(df)):
        stat = df.iloc[i,5]
        if stat == 'Passing Yards':
            df.at[i,'4for4_proj'] = df.iloc[i,18]
        elif stat == 'Fantasy Points':
            df.at[i,'4for4_proj'] = df.iloc[i,15]
        elif stat == 'Receptions':
            df.at[i,'4for4_proj'] = df.iloc[i,24]
        elif stat == 'Receiving Yards':
            df.at[i,'4for4_proj'] = df.iloc[i,25]
        elif stat == 'Rushing Yards':
            df.at[i,'4for4_proj'] = df.iloc[i,22]
     
    df = df[df['Season'].notna()]
    df = df[['game','contest','player_num','player_name','stat_name','stat_val','4for4_proj']]
    df['pct_diff'] = (df['4for4_proj'] / df['stat_val'].astype(float)) - 1
    df['gt_15'] = (abs(df['pct_diff']) > 0.15).astype(int)
    
    return df

if __name__ == "__main__":
    url = 'https://www.monkeyknifefight.com/newgame/NFL' 
    mkf_df = run_scrape(url)
    
    rank_file = '4for4_W10_projections.csv'
    mkf_rank_df = merge_rankings(mkf_df,rank_file)
    
    clean_df = clean_rankings(mkf_rank_df)
    
    #Write to csv
    output = 'week10'
    clean_df.to_csv(output+".csv")
    