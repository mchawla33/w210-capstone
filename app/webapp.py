import streamlit as st
import numpy as np
import pandas as pd
import csv
import boto3
import requests
from PIL import Image

def getdata(url, filename):
    ''' get csv data via api gateway
        url: api gateway's invoke URL
        filename: csv filename to get 
    '''
    payload = {"filename": filename}
    resp = requests.post(url=url, json=payload)
    return resp


def main():    

    # aws s3 bucket
    bucketname = "capstone-nfl-data-jb"
    # api gateway invoke url
    url = "https://quubx4ry2b.execute-api.us-west-2.amazonaws.com/dev/"
    # teams
    #teams = ['ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE', 'DAL', 'DEN','DET', 'GB', 
    #    'HOU', 'IND', 'JAX', 'KC', 'LA', 'LAC', 'LV', 'MIA', 'MIN', 'NE', 'NO', 'NYG', 'NYJ', 
    #    'PHI', 'PIT', 'SEA', 'SF', 'TB', 'TEN', 'WAS']
    
    namemap = {'Arizona Cardinals' : 'ARI', 'Atlanta Falcons' : 'ATL', 'Baltimore Ravens' : 'BAL', 'Buffalo Bills' : 'BUF', 
        'Carolina Panthers' : 'CAR', 'Chicago Bears' : 'CHI', 'Cincinnati Bengals' : 'CIN', 'Cleveland Browns' : 'CLE', 
        'Dallas Cowboys' : 'DAL', 'Denver Broncos' : 'DEN', 'Detroit Lions' : 'DET', 'Green Bay Packers' : 'GB', 
        'Houston Texans' : 'HOU', 'Indianapolis Colts' : 'IND', 'Jacksonville Jaguars' : 'JAX', 'Kansas City Chiefs' : 'KC', 
        'Los Angeles Rams' : 'LA', 'Los Angeles Chargers' : 'LAC', 'Las Vegas Raiders' : 'LV', 'Miami Dolphins' : 'MIA', 
        'Minnesota Vikings' : 'MIN', 'New England Patriots' : 'NE', 'New Orleans Saints' : 'NO', 'New York Giants' : 'NYG', 
        'New York Jets' : 'NYJ', 'Philadelphia Eagles' : 'PHI', 'Pittsburgh Steelers' : 'PIT', 'Seattle Seahawks' : 'SEA', 
        'San Francisco 49ers' : 'SF', 'Tampa Bay Buccaneers' : 'TB', 'Tennessee Titans' : 'TEN', 'Washington Commanders' : 'WAS'}
    
    fullnames = list(namemap.keys())

    # main logo
    hcol1, hcol2, hcol3 = st.columns([3,1,1])
    with hcol1:
        logo = "images/plaicall.png"
        image = Image.open(logo)
        st.image(image, width=400)
    

    # input menus (left sidebar)
    with st.sidebar:
        # your team
        st.write('Your Team (Offense)')
        deftxt = 'Select a team'
        selections = tuple([deftxt] + fullnames)
        sel = st.selectbox('Your Team', selections, label_visibility="collapsed")
        our = namemap.get(sel)
        if our == None:
            st.warning('No team selected')
            st.stop()

        st.write('')
        st.write('')
        # opponent
        st.write('Opponent (Defense)')
        deftxt = 'Select a team'
        fullnames.remove(sel)
        selections = tuple([deftxt] + fullnames)
        sel = st.selectbox('Opponent', selections, label_visibility="collapsed")
        opp = namemap.get(sel)
        if opp == None:
            st.warning('No team selected')
            st.stop()

    # matchup picture
    with hcol2:
        ourimgfile = "images/"+our+".png"
        ourimg = Image.open(ourimgfile)
        st.write("###### Offensive Team")
        st.image(ourimg, width=100)
    with hcol3:
        oppimgfile = "images/"+opp+".png"
        oppimg = Image.open(oppimgfile)
        st.write("###### Defensive Team")
        st.image(oppimg, width=100)

    # csv filename
    filename = our+"_"+opp+".csv"

    try:
        
        # create dataframe from the s3 data
        r = getdata(url=url, filename=filename)
        data = eval(r.json()['body'])
        d = [ d.split(',')[1:] for d in data[1:] ]
        col_index = data[0].split(',')[1:]
        df = pd.DataFrame(data=d, columns=col_index)
        # convert types to the original csv data type
        df.qtr = df.qtr.astype('float64')
        df.down = df.down.astype('float64')
        df.poss_differential = df.poss_differential.astype('float64')
        df.red_zone = df.red_zone.astype('int64')
        df.pred_formation_1 = df.pred_formation_1.astype('int64')
        df.pred_formation_2 = df.pred_formation_2.astype('int64')
        df.pred_formation_3 = df.pred_formation_3.astype('int64')

        # filter column arrangement
        c1, c2, c3 = st.columns(3)
        # quarter filter
        with c1:
            quarter = st.radio("Quarter", ('Q1', 'Q2', 'Q3', 'Q4'))
        # score difference filter
        with c2:
            score = st.radio("Score difference (Possession)", ('-2+', '-1', 'Tied', '+1', '+2+'), index=2)

        # mapping between UI filter menus (quarter and score selections) and the csv
        fmap = {'Q1': 1, 'Q2': 2, 'Q3': 2, 'Q4': 4,
                '-2+': -2, '-1': -1, 'Tied': 0, '+1': 1, '+2+': 2} 

        # select subset of csv based on quarter and score selections
        qtr_sel = fmap[quarter]
        poss_sel = fmap[score]
        cond = (df['qtr']==qtr_sel) & (df['poss_differential']==poss_sel)
        subdf = df[cond]
        outdf = []

        # table header names
        hdr = [['1st & XL (15-20)', '2nd & XL (10+)', '3rd & XL (10+)'],
            ['1st & 10', '2nd & Long (6-10)', '3rd & Long (6-10)'],
            ['1st & Short (1-5)', '2nd & Short (1-5)', '3rd & Short (1-5)'],
            ['Red Zone (+20 - +11)',  'Red Zone (+10 - +6)', '4th & Long (6-10)'],
            ['Red Zone (+3 - +5)', 'Red Zone (<3)', '4th & Short (1-5)']]

        # arrange set of 15 tables given qarter and score selections
        for h in hdr:
            rowtables = []
            for c in h:
                d = subdf[subdf['title']==c].loc[:, ['pred_formation_1', 'pred_formation_2', 'pred_formation_3']].values.tolist()[0]
                row_index = subdf[subdf['title']==c].loc[:, ['pred_play_1', 'pred_play_2', 'pred_play_3']].values.tolist()[0]
                col_index = [c]
                rowtables.append(pd.DataFrame(data=d, index=row_index, columns=col_index))
            outdf.append(rowtables)
            
        # display tables

        # table background colors
        backcolors = [['greenyellow','cornsilk','orange'],
                      ['greenyellow','cornsilk','orange'],
                      ['greenyellow','cornsilk','orange'],
                      ['orangered','orangered','lavender'],
                      ['orangered','orangered','lavender']]

        ncols = 3
        nrows = 5
        for r in range(nrows):
            tables = st.columns(ncols, gap="medium")
            for c in range(ncols):
                # table styling
                header_properties = [('font-size', '15px'),('text-align', 'left'),
                                    ('color', 'black'),('font-weight', 'bold'),
                                    ('background', 'white'),('border', '1.3px solid')]
                index_properties = [('font-size', '15px'),('text-align', 'left'),
                                    ('color', 'black'),('font-weight', 'normal'),
                                    ('background', backcolors[r][c]),('border', '1.3px solid')]
                cell_properties = [('font-size', '15px'),('text-align', 'right'),
                                    ('color', 'black'),('font-weight', 'normal'),
                                    ('background', backcolors[r][c]),('border', '1.3px solid')]                                  
                dfstyle = [{"selector": "th", "props": header_properties},
                           {"selector": "th.row_heading", "props": index_properties},
                           {"selector": "td", "props": cell_properties}]
                styler_df = (outdf[r][c].style.set_table_styles(dfstyle))           
                tables[c].table(styler_df)         
    except:
        st.write(our+' vs '+opp+' data not found')


if __name__ == "__main__":
    st.set_page_config(
        page_title="Ex-stream-ly Cool App",
        page_icon="🧊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    main()