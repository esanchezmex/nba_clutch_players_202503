import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from nba_api.stats.endpoints import leaguedashplayerclutch, leaguedashplayerstats
from nba_api.stats.static import players
import seaborn as sns
import time

def compare_net_rating(player_name, seasons=None):
    """
    Compare a player's NET_RATING across regular season, clutch, and playoffs.
    
    Parameters:
    -----------
    player_name : str
        Full name of the player (e.g., 'Chris Paul')
    seasons : list, optional
        List of seasons to analyze (e.g., ['2020-21', '2021-22'])
        If None, will use the last 5 seasons
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with NET_RATING comparison
    """
    if seasons is None:
        # Default to last 5 seasons if not specified
        current_year = 2024  # Update this as needed
        seasons = [f"{year-1}-{str(year)[-2:]}" for year in range(current_year-4, current_year+1)]
    
    print(f"Comparing {player_name}'s NET_RATING for seasons: {', '.join(seasons)}")
    
    # Get player ID
    player_dict = players.find_players_by_full_name(player_name)
    if not player_dict:
        print(f"Could not find player ID for {player_name}")
        return None
    elif len(player_dict) > 1:
        print(f"Multiple players found for {player_name}:")
        for i, player in enumerate(player_dict):
            print(f"{i}: {player['full_name']} (ID: {player['id']}, Active: {player['is_active']})")
        
        # Prompt user to select a player
        selection = input("Enter the number of the player you want to analyze: ")
        try:
            selection = int(selection)
            if 0 <= selection < len(player_dict):
                player_id = player_dict[selection]['id']
                print(f"Selected player ID: {player_id}")
            else:
                print(f"Invalid selection. Please enter a number between 0 and {len(player_dict)-1}")
                return None
        except ValueError:
            print("Invalid input. Please enter a number.")
            return None
    else:
        player_id = player_dict[0]['id']
        print(f"Found player ID: {player_id}")
    
    # Initialize results
    results = []
    
    # Process each season
    for season in seasons:
        print(f"\nProcessing season: {season}")
        season_data = {'Season': season}
        
        # 1. Get regular season stats
        try:
            regular_stats = leaguedashplayerstats.LeagueDashPlayerStats(
                season=season,
                season_type_all_star='Regular Season',
                measure_type_detailed_defense='Advanced'
            )
            regular_df = regular_stats.get_data_frames()[0]
            player_regular = regular_df[regular_df['PLAYER_NAME'] == player_name]
            
            if not player_regular.empty:
                season_data['Regular Season'] = player_regular['NET_RATING'].iloc[0]
            else:
                print(f"No regular season data found for {player_name} in {season}")
                season_data['Regular Season'] = None
        except Exception as e:
            print(f"Error getting regular season stats: {e}")
            season_data['Regular Season'] = None
        
        # 2. Get clutch stats
        try:
            clutch_stats = leaguedashplayerclutch.LeagueDashPlayerClutch(
                season=season,
                season_type_all_star='Regular Season',
                measure_type_detailed_defense='Advanced',
                clutch_time='Last 5 Minutes',
                point_diff='5'
            )
            clutch_df = clutch_stats.get_data_frames()[0]
            player_clutch = clutch_df[clutch_df['PLAYER_NAME'] == player_name]
            
            if not player_clutch.empty:
                season_data['Clutch'] = player_clutch['NET_RATING'].iloc[0]
            else:
                print(f"No clutch data found for {player_name} in {season}")
                season_data['Clutch'] = None
        except Exception as e:
            print(f"Error getting clutch stats: {e}")
            season_data['Clutch'] = None
        
        # 3. Get playoff stats
        try:
            playoff_stats = leaguedashplayerstats.LeagueDashPlayerStats(
                season=season,
                season_type_all_star='Playoffs',
                measure_type_detailed_defense='Advanced'
            )
            playoff_df = playoff_stats.get_data_frames()[0]
            player_playoff = playoff_df[playoff_df['PLAYER_NAME'] == player_name]
            
            if not player_playoff.empty:
                season_data['Playoffs'] = player_playoff['NET_RATING'].iloc[0]
            else:
                print(f"No playoff data found for {player_name} in {season}")
                season_data['Playoffs'] = None
        except Exception as e:
            print(f"Error getting playoff stats: {e}")
            season_data['Playoffs'] = None
        
        # Add to results
        results.append(season_data)
        
        # Add delay to avoid rate limiting
        time.sleep(1)
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    # Visualize the results
    visualize_net_rating_comparison(results_df, player_name)
    
    return results_df

def visualize_net_rating_comparison(df, player_name):
    """
    Visualize NET_RATING comparison.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with NET_RATING comparison
    player_name : str
        Player name for the title
    """
    # Set up the style
    sns.set_style("whitegrid")
    plt.figure(figsize=(12, 8))
    
    # Melt the DataFrame for easier plotting
    df_melted = df.melt(id_vars=['Season'], var_name='Game Situation', value_name='NET_RATING')
    
    # Create the plot
    sns.barplot(data=df_melted, x='Season', y='NET_RATING', hue='Game Situation')
    
    # Add labels and title
    plt.xlabel('Season')
    plt.ylabel('NET_RATING')
    plt.title(f"{player_name}'s NET_RATING Comparison")
    plt.xticks(rotation=45)
    
    # Add a horizontal line at 0
    plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
    
    # Adjust layout and show
    plt.tight_layout()
    plt.show()
    
    # Print summary
    print("\nNET_RATING Summary:")
    print(df)
    
    # Calculate averages
    print("\nAverage NET_RATING:")
    print(df[['Regular Season', 'Clutch', 'Playoffs']].mean())

if __name__ == "__main__":
    # Compare Chris Paul's NET_RATING
    compare_net_rating('Chris Paul', seasons=['2017-18', '2018-19', '2019-20', '2020-21', '2021-22'])
    
    # You can uncomment the following lines to analyze other players
    # compare_net_rating('LeBron James', seasons=['2017-18', '2018-19', '2019-20', '2020-21', '2021-22'])
    # compare_net_rating('Stephen Curry', seasons=['2017-18', '2018-19', '2019-20', '2020-21', '2021-22']) 