import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from nba_api.stats.endpoints import leaguedashplayerclutch, leaguedashplayerstats, playerdashptshots
from nba_api.stats.endpoints import commonplayerinfo, playerdashboardbygeneralsplits, shotchartdetail
from nba_api.stats.static import players
import seaborn as sns
import time

def analyze_clutch_player(player_name, seasons=None):
    """
    Comprehensive analysis of a player's clutch performance in regular season.
    
    Parameters:
    -----------
    player_name : str
        Full name of the player (e.g., 'Chris Paul')
    seasons : list, optional
        List of seasons to analyze (e.g., ['2020-21', '2021-22'])
        If None, will use the last 5 seasons
        
    Returns:
    --------
    dict
        Dictionary containing all analysis results and DataFrames
    """
    if seasons is None:
        # Default to last 5 seasons if not specified
        current_year = 2024  # Update this as needed
        seasons = [f"{year-1}-{str(year)[-2:]}" for year in range(current_year-4, current_year+1)]
    
    print(f"Analyzing {player_name}'s clutch performance for seasons: {', '.join(seasons)}")
    
    # Initialize results dictionary
    results = {
        'player_name': player_name,
        'seasons': seasons,
        'player_info': None,
        'clutch_stats': [],
        'shot_distance': [],
        'regular_vs_clutch': []
    }
    
    # 1. Get player info (physical attributes)
    try:
        # First, get the player ID using the static players endpoint
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
        
        # Now get player info using the ID
        player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        info_df = player_info.get_data_frames()[0]
        
        if not info_df.empty:
            results['player_info'] = {
                'height': info_df['HEIGHT'].iloc[0],
                'weight': info_df['WEIGHT'].iloc[0],
                'player_id': player_id
            }
        else:
            print(f"Could not find player info for {player_name}")
            return None
    except Exception as e:
        print(f"Error getting player info: {e}")
        return None
    
    # Process each season
    for season in seasons:
        print(f"\nProcessing season: {season}")
        season_data = {'season': season}
        
        # Need to wait to avoid API rate limiting
        time.sleep(5)

        # 2. Get clutch stats
        try:
            clutch_stats = leaguedashplayerclutch.LeagueDashPlayerClutch(
                season=season,
                season_type_all_star='Regular Season',
                measure_type_detailed_defense='Base',  # Use Base for shooting percentages
                clutch_time='Last 5 Minutes',
                point_diff='5',
                per_mode_detailed='Per36'
            )
            clutch_df = clutch_stats.get_data_frames()[0]
            player_clutch = clutch_df[clutch_df['PLAYER_NAME'] == player_name]
            
            if not player_clutch.empty:
                # Basic clutch stats
                season_data['clutch_basic'] = {
                    'gp': player_clutch['GP'].iloc[0],
                    'min': player_clutch['MIN'].iloc[0],
                    'pts': player_clutch['PTS'].iloc[0],
                    'fg_pct': player_clutch['FG_PCT'].iloc[0],
                    'fg3_pct': player_clutch['FG3_PCT'].iloc[0],
                    'ft_pct': player_clutch['FT_PCT'].iloc[0],
                    'ast': player_clutch['AST'].iloc[0],
                    'tov': player_clutch['TOV'].iloc[0],
                    'stl': player_clutch['STL'].iloc[0],
                    'blk': player_clutch['BLK'].iloc[0],
                    'plus_minus': player_clutch['PLUS_MINUS'].iloc[0]
                }
                
                # Calculate additional ratios
                if player_clutch['TOV'].iloc[0] > 0:
                    season_data['clutch_basic']['ast_to_tov'] = player_clutch['AST'].iloc[0] / player_clutch['TOV'].iloc[0]
                else:
                    season_data['clutch_basic']['ast_to_tov'] = player_clutch['AST'].iloc[0] if player_clutch['AST'].iloc[0] > 0 else 0
                
                # Need to wait to avoid API rate limiting
                time.sleep(5)
                # Get advanced clutch stats
                clutch_adv = leaguedashplayerclutch.LeagueDashPlayerClutch(
                    season=season,
                    season_type_all_star='Regular Season',
                    measure_type_detailed_defense='Advanced',
                    clutch_time='Last 5 Minutes',
                    point_diff='5',
                    per_mode_detailed='Per36'
                )
                clutch_adv_df = clutch_adv.get_data_frames()[0]
                player_clutch_adv = clutch_adv_df[clutch_adv_df['PLAYER_NAME'] == player_name]
                
                if not player_clutch_adv.empty:
                    season_data['clutch_advanced'] = {
                        'usg_pct': player_clutch_adv['USG_PCT'].iloc[0],
                        'ts_pct': player_clutch_adv['TS_PCT'].iloc[0],
                        'net_rating': player_clutch_adv['NET_RATING'].iloc[0],
                        'off_rating': player_clutch_adv['OFF_RATING'].iloc[0],
                        'def_rating': player_clutch_adv['DEF_RATING'].iloc[0],
                        'ast_pct': player_clutch_adv['AST_PCT'].iloc[0] if 'AST_PCT' in player_clutch_adv.columns else None,
                        'pie': player_clutch_adv['PIE'].iloc[0]
                    }
            else:
                print(f"No clutch data found for {player_name} in {season}")
                continue
                
            # 3. Get shot distance data using shotchartdetail
            try:
                # Need to wait to avoid API rate limiting
                time.sleep(5)
                
                # Get shot chart data
                shot_chart = shotchartdetail.ShotChartDetail(
                    player_id=player_id,
                    team_id=0,
                    season_nullable=season,
                    season_type_all_star='Regular Season',
                    context_measure_simple='FGA',
                    clutch_time_nullable='Last 5 Minutes',
                    point_diff_nullable='5'
                )
                
                shot_df = shot_chart.get_data_frames()[0]
                
                if not shot_df.empty:
                    # Create distance bins
                    shot_df['DISTANCE_BIN'] = pd.cut(
                        shot_df['SHOT_DISTANCE'], 
                        bins=[0, 3, 10, 16, 23, 40], 
                        labels=['0-3 ft', '3-10 ft', '10-16 ft', '16-23 ft', '23+ ft']
                    )
                    
                    # Group by distance bin
                    distance_stats = shot_df.groupby('DISTANCE_BIN').agg({
                        'SHOT_MADE_FLAG': ['count', 'sum']
                    })
                    
                    # Calculate percentages
                    distance_stats.columns = ['FGA', 'FGM']
                    distance_stats['FG_PCT'] = distance_stats['FGM'] / distance_stats['FGA']
                    distance_stats['FGA_FREQUENCY'] = distance_stats['FGA'] / distance_stats['FGA'].sum()
                    
                    # Store in results
                    season_data['shot_distance'] = {}
                    for idx, row in distance_stats.iterrows():
                        group_name = str(idx).lower().replace(' ', '_')
                        season_data['shot_distance'][group_name] = {
                            'fgm': row['FGM'],
                            'fga': row['FGA'],
                            'fg_pct': row['FG_PCT'],
                            'pct_fga': row['FGA_FREQUENCY']
                        }
                # Need to wait to avoid API rate limiting
                time.sleep(5)
                
                # 4. Compare regular season overall vs clutch
                regular_stats = leaguedashplayerstats.LeagueDashPlayerStats(
                    season=season,
                    season_type_all_star='Regular Season',
                    measure_type_detailed_defense='Base',
                    per_mode_detailed='Per36'
                )
                regular_df = regular_stats.get_data_frames()[0]
                player_regular = regular_df[regular_df['PLAYER_NAME'] == player_name]
                
                if not player_regular.empty and not player_clutch.empty:
                    # # Convert clutch to per game for fair comparison
                    # clutch_per_game = player_clutch.copy()
                    # gp = clutch_per_game['GP'].iloc[0]
                    # if gp > 0:
                    #     for col in ['PTS', 'FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 'AST', 'TOV', 'STL', 'BLK']:
                    #         if col in clutch_per_game.columns:
                    #             clutch_per_game[col] = clutch_per_game[col] / gp
                    
                    season_data['regular_vs_clutch'] = {
                        'regular': {
                            'pts': player_regular['PTS'].iloc[0],
                            'fg_pct': player_regular['FG_PCT'].iloc[0],
                            'fg3_pct': player_regular['FG3_PCT'].iloc[0],
                            'ft_pct': player_regular['FT_PCT'].iloc[0],
                            'ast': player_regular['AST'].iloc[0],
                            'tov': player_regular['TOV'].iloc[0],
                            'ast_to_tov': player_regular['AST'].iloc[0] / player_regular['TOV'].iloc[0] if player_regular['TOV'].iloc[0] > 0 else player_regular['AST'].iloc[0]
                        },
                        'clutch': {
                            'pts': player_clutch['PTS'].iloc[0],
                            'fg_pct': player_clutch['FG_PCT'].iloc[0],
                            'fg3_pct': player_clutch['FG3_PCT'].iloc[0],
                            'ft_pct': player_clutch['FT_PCT'].iloc[0],
                            'ast': player_clutch['AST'].iloc[0],
                            'tov': player_clutch['TOV'].iloc[0],
                            'ast_to_tov': season_data['clutch_basic']['ast_to_tov']
                        }
                    }
                
            except Exception as e:
                print(f"Error getting shot distance data: {e}")
            
            # Add season data to results
            results['clutch_stats'].append(season_data)
            
        except Exception as e:
            print(f"Error processing season {season}: {e}")
    
    # 5. Visualize the results
    if results['clutch_stats']:
        visualize_player_analysis(results)
    
    return results

def visualize_player_analysis(results):
    """
    Create visualizations for player analysis results
    
    Parameters:
    -----------
    results : dict
        Results dictionary from analyze_clutch_player function
    """
    player_name = results['player_name']
    
    # Set up the style
    sns.set_style("whitegrid")
    plt.figure(figsize=(20, 15))
    
    # 1. Shooting percentages over seasons
    plt.subplot(2, 2, 1)
    seasons = []
    fg_pcts = []
    fg3_pcts = []
    ft_pcts = []
    
    for season_data in results['clutch_stats']:
        if 'clutch_basic' in season_data:
            seasons.append(season_data['season'])
            fg_pcts.append(season_data['clutch_basic']['fg_pct'])
            fg3_pcts.append(season_data['clutch_basic']['fg3_pct'])
            ft_pcts.append(season_data['clutch_basic']['ft_pct'])
    
    x = np.arange(len(seasons))
    width = 0.25
    
    plt.bar(x - width, fg_pcts, width, label='FG%')
    plt.bar(x, fg3_pcts, width, label='3FG%')
    plt.bar(x + width, ft_pcts, width, label='FT%')
    
    plt.xlabel('Season')
    plt.ylabel('Percentage')
    plt.title(f"{player_name}'s Clutch Shooting Percentages")
    plt.xticks(x, seasons, rotation=45)
    plt.legend()
    
   # 2. Regular vs Clutch comparison (all selected seasons)
    if results['clutch_stats']:
        plt.subplot(2, 2, 2)
        
        # Calculate averages across all seasons
        metrics = ['pts', 'fg_pct', 'fg3_pct', 'ft_pct', 'ast', 'tov', 'ast_to_tov']
        regular_avgs = {m: 0 for m in metrics}
        clutch_avgs = {m: 0 for m in metrics}
        count = 0
        
        for season_data in results['clutch_stats']:
            if 'regular_vs_clutch' in season_data:
                count += 1
                for m in metrics:
                    regular_avgs[m] += season_data['regular_vs_clutch']['regular'][m]
                    clutch_avgs[m] += season_data['regular_vs_clutch']['clutch'][m]
        
        # Calculate the averages
        if count > 0:
            # Separate percentage metrics from counting stats
            pct_metrics = ['fg_pct', 'fg3_pct', 'ft_pct']
            count_metrics = [m for m in metrics if m not in pct_metrics]
            
            # Create figure with two y-axes
            ax1 = plt.gca()
            ax2 = ax1.twinx()
            
            # Plot counting stats
            x_count = np.arange(len(count_metrics))
            width = 0.35
            regular_count_vals = [regular_avgs[m] / count for m in count_metrics]
            clutch_count_vals = [clutch_avgs[m] / count for m in count_metrics]
            
            ax1.bar(x_count - width/2, regular_count_vals, width, label='Regular', color='royalblue')
            ax1.bar(x_count + width/2, clutch_count_vals, width, label='Clutch', color='orangered')
            
            # Plot percentage stats
            x_pct = np.arange(len(count_metrics), len(count_metrics) + len(pct_metrics))
            regular_pct_vals = [regular_avgs[m] / count for m in pct_metrics]
            clutch_pct_vals = [clutch_avgs[m] / count for m in pct_metrics]
            
            ax2.bar(x_pct - width/2, regular_pct_vals, width, label='Regular', color='lightblue')
            ax2.bar(x_pct + width/2, clutch_pct_vals, width, label='Clutch', color='lightsalmon')
            
            # Set labels and title
            ax1.set_xlabel('Metric')
            ax1.set_ylabel('Value (Per 36 Minutes)')
            ax2.set_ylabel('Percentage')
            
            seasons_range = f"{results['seasons'][0]} to {results['seasons'][-1]}"
            plt.title(f"{player_name}'s Regular vs Clutch Performance (Per 36, {seasons_range})")
            
            # Set x-ticks for all metrics
            all_x = np.arange(len(metrics))
            plt.xticks(all_x, [m.upper().replace('_', ' ') for m in count_metrics + pct_metrics], rotation=45)
            
            # Add legends
            ax1.legend(loc='upper left')
            ax2.legend(loc='upper right')
    
    # 3. Shot distance breakdown (season average from clutch stats)
    if results['clutch_stats']:
        plt.subplot(2, 2, 3)
        
        # Initialize dictionaries to store averages
        distance_data = {}
        
        # Collect data from all seasons
        for season_data in results['clutch_stats']:
            if 'shot_distance' in season_data:
                for distance, stats in season_data['shot_distance'].items():
                    if distance not in distance_data:
                        distance_data[distance] = {'pct_fga': 0, 'fg_pct': 0, 'count': 0, 'fga': 0}
                    
                    distance_data[distance]['pct_fga'] += stats['pct_fga']
                    # Only add fg_pct if shots were attempted
                    if stats.get('fga', 0) > 0:
                        distance_data[distance]['fg_pct'] += stats['fg_pct']
                        distance_data[distance]['fga'] += stats.get('fga', 0)
                    distance_data[distance]['count'] += 1
        
        # Calculate averages
        distances = []
        pct_fga = []
        fg_pct = []
        valid_indices = []  # Track indices with valid FG% data
        
        for distance, stats in distance_data.items():
            if stats['count'] > 0:
                distances.append(distance)
                pct_fga.append(stats['pct_fga'] / stats['count'])
                # Only calculate average if there were shots attempted
                if stats.get('fga', 0) > 0:
                    fg_pct.append(stats['fg_pct'] / stats['count'])
                    valid_indices.append(len(distances) - 1)
                else:
                    fg_pct.append(None)  # Use None for missing data
        
        # Sort distances properly
        distance_order = ['0-3_ft', '3-10_ft', '10-16_ft', '16-23_ft', '23+_ft']
        sorted_indices = [distances.index(d) for d in distance_order if d in distances]
        distances = [distances[i] for i in sorted_indices]
        pct_fga = [pct_fga[i] for i in sorted_indices]
        
        # Remap valid indices and fg_pct after sorting
        old_to_new = {old: new for new, old in enumerate(sorted_indices)}
        valid_indices = [old_to_new[i] for i in valid_indices if i in old_to_new]
        fg_pct = [fg_pct[i] for i in sorted_indices]
        
        # Create a figure with two y-axes
        ax1 = plt.gca()
        ax2 = ax1.twinx()
        
        # Plot data
        x = np.arange(len(distances))
        ax1.bar(x, pct_fga, 0.4, color='skyblue', label='% of FGA')
        
        # Plot only valid FG% points with markers
        valid_x = []
        valid_fg_pct = []
        for i in range(len(x)):
            if fg_pct[i] is not None:
                valid_x.append(x[i])
                valid_fg_pct.append(fg_pct[i])
        
        # Plot points with large markers
        ax2.scatter(valid_x, valid_fg_pct, color='red', s=80, zorder=3, label='FG%')
        
        # Connect points if they are adjacent
        if len(valid_x) > 1:
            for i in range(len(valid_x)-1):
                ax2.plot(valid_x[i:i+2], valid_fg_pct[i:i+2], 'r-', linewidth=2)
        
        # Set labels and title
        ax1.set_xlabel('Shot Distance')
        ax1.set_ylabel('% of Field Goal Attempts', color='skyblue')
        ax2.set_ylabel('Field Goal %', color='red')
        seasons_range = f"{results['seasons'][0]} to {results['seasons'][-1]}"
        plt.title(f"{player_name}'s Clutch Shot Distance Breakdown ({seasons_range})")
        plt.xticks(x, [d.replace('_', ' ').title() for d in distances], rotation=45)
        
        # Add legends
        ax1.legend(loc='upper left')
        ax2.legend(loc='upper right')
    
    # 4. Advanced metrics over seasons
    plt.subplot(2, 2, 4)
    seasons = []
    net_ratings = []
    usg_pcts = []
    ts_pcts = []
    
    for season_data in results['clutch_stats']:
        if 'clutch_advanced' in season_data:
            seasons.append(season_data['season'])
            net_ratings.append(season_data['clutch_advanced']['net_rating'])
            usg_pcts.append(season_data['clutch_advanced']['usg_pct'] * 100)  # Convert to percentage
            ts_pcts.append(season_data['clutch_advanced']['ts_pct'] * 100)    # Convert to percentage
    
    x = np.arange(len(seasons))
    
    plt.plot(x, net_ratings, 'bo-', label='NET Rating')
    plt.plot(x, usg_pcts, 'go-', label='USG%')
    plt.plot(x, ts_pcts, 'ro-', label='TS%')
    
    plt.xlabel('Season')
    plt.ylabel('Value')
    plt.title(f"{player_name}'s Advanced Clutch Metrics")
    plt.xticks(x, seasons, rotation=45)
    plt.legend()
    
    plt.tight_layout()
    plt.show()
    
    # Print player info
    if results['player_info']:
        print(f"\n{player_name}'s Profile:")
        print(f"Height: {results['player_info']['height']}")
        print(f"Weight: {results['player_info']['weight']} lbs")
    
    # Print summary of clutch performance
    print("\nClutch Performance Summary:")
    for season_data in results['clutch_stats']:
        if 'clutch_basic' in season_data and 'clutch_advanced' in season_data:
            print(f"\n{season_data['season']}:")
            print(f"  Games: {season_data['clutch_basic']['gp']}, Minutes: {season_data['clutch_basic']['min']}")
            print(f"  Shooting: FG%={season_data['clutch_basic']['fg_pct']:.3f}, 3P%={season_data['clutch_basic']['fg3_pct']:.3f}, FT%={season_data['clutch_basic']['ft_pct']:.3f}")
            print(f"  Playmaking: AST={season_data['clutch_basic']['ast']:.1f}, TOV={season_data['clutch_basic']['tov']:.1f}, AST/TOV={season_data['clutch_basic']['ast_to_tov']:.2f}")
            print(f"  Advanced: NET RTG={season_data['clutch_advanced']['net_rating']:.1f}, USG%={season_data['clutch_advanced']['usg_pct']*100:.1f}%, TS%={season_data['clutch_advanced']['ts_pct']*100:.1f}%")

# Example usage
# analyze_clutch_player('Chris Paul')
