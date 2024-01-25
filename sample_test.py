                    # Create columns
                col3, col4,col5,col6 = container.columns(4)
                channels_quary = 'select chanel_name from channels'
                videos_quary =  """
                SELECT v.video_name, c.channel_name
                FROM videos v
                INNER JOIN channels c ON v.playlist_id = c.playlist_id;
                """
                # Sidebar input widgets
                selected_channel = col3.multiselect('Select Channel:', sorted(visualise.sql_query('select chanel_name from channels')),help='Select the Channel')
                selected_quarters = col4.multiselect('Select Quarter:', sorted(visualise.sql_query(f'select video_name from videos {selected_channel}')))

                # Check if 'state' is a column in the DataFrame
                if 'state' in df.columns:
                    selected_state = col5.multiselect('Select State/UT:', sorted(df['state'].unique()),default = ['karnataka'])
                    entity_type = col6.selectbox('Select Entity Type:', sorted(df['entity_type'].unique()))


                    # if filter_data: