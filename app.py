import streamlit as st
import pandas as pd
import json
import pickle
import plotly.graph_objects as go


@st.cache_data
def convert_df(df, file_index=False):
    return df.to_csv(index=file_index).encode('utf-8')


def display_download(df, file_name='report', hide_index=True, file_index=False):
    st.dataframe(
        data=df,
        use_container_width=True,
        hide_index=hide_index,
    )

    encoded_data = convert_df(df, file_index)
    st.download_button(
        label='Download data as .csv',
        data=encoded_data,
        file_name=f'{file_name}.csv',
        mime='text/csv',
        key=f'{file_name.lower().replace(" ", "_")}_download'
    )


def group_dataframe(df, group_cols, target_cols):
    grouped_df = df.groupby(group_cols)[target_cols] \
                   .nunique() \
                   .sort_values(ascending=False) \
                   .reset_index()
    return grouped_df


def piechart_plot(df, labels, values):
    config = {"displayModeBar": False}

    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=df[labels],
        values=df[values],
        hole=0.3,
        hoverinfo='label+value+percent'
    ))
    fig.update_layout(
        width=300,
        height=300
    )

    st.plotly_chart(fig, use_container_width=True, config=config)


def rawdata_preprocess(uploaded_file):
    data = pd.read_excel(uploaded_file, skiprows=2).dropna(subset='Booking Date')
    data['Booking Date'] = data['Booking Date'].apply(lambda x: x[:-6])
    data['Booking Date'] = pd.to_datetime(data['Booking Date'])
    data['Arrival Date'] = pd.to_datetime(data['Arrival Date'])
    data['Name ID'] = data['Contact Name'].apply(lambda x: x.lower().replace(' ', ''))
    data = data[data['Status'] != 'Cancelled']
    data = data.drop(['Email', 'Phone No'], axis=1)
    data = data.astype({"Booking No": "string"})

    return data


def run():
    st.set_page_config(
        page_title='Reporting Tool',
        page_icon="📊",
        layout='centered',  # centered, wide
        initial_sidebar_state='auto',  # auto, expanded, collapsed
    )

    title_cols = st.columns((1, 1))
    with title_cols[0]:
        st.title('Springhill Report')
    with title_cols[1]:
        st.subheader(' ')
        st.subheader(' ')
        date_range_ph = st.empty()

    uploaded_file = st.file_uploader(
        label='Select a file',
        type='xlsx',
        accept_multiple_files=False,
    )

    # -----------------------------------------------File Management----------------------------------------------- #
    if uploaded_file:
        data = rawdata_preprocess(uploaded_file)
        start_date = min(data['Booking Date']).strftime('%Y-%m-%d')
        end_date = max(data['Booking Date']).strftime('%Y-%m-%d')
        date_range = f"""Date Range: **_{start_date} - {end_date}_**"""
        date_range_ph.markdown(date_range)

        with open('./analysis.json', 'r') as f:
            analysis_list = json.load(f).get('analysis')

        # --------------------------------------------Return-------------------------------------------- #
        st.divider()
        st.subheader(analysis_list[0])
        df_return = group_dataframe(data, 'Name ID', 'Booking No')
        df_return['Status'] = df_return['Booking No'].apply(lambda x: 'Return' if x > 1 else 'First-time')
        df_return = group_dataframe(df_return, 'Status', 'Name ID')
        df_return.columns = ['Status', 'Number of Guest']
        # piechart_plot(df_return, labels='Status', values='Number of Guest')
        df_return.loc[df_return.shape[0]] = df_return.sum()
        df_return.iloc[-1, 0] = 'Grand Total'
        display_download(df_return, 'Return')

        # --------------------------------------------Room Type-------------------------------------------- #
        st.divider()
        st.subheader(analysis_list[1])
        df_room = group_dataframe(data, 'Room Type', 'Booking No')
        df_room.columns = ['Room Type', 'Number of Booking']
        df_room.loc[df_room.shape[0]] = df_room.sum()
        df_room.iloc[-1, 0] = 'Grand Total'
        display_download(df_room, 'Room Type')

        # --------------------------------------------People-------------------------------------------- #
        st.divider()
        st.subheader(analysis_list[2])
        df_ppl = data[['Booking No', 'Room Type', 'NoAdult']].copy()
        df_ppl['People Type'] = df_ppl['NoAdult'].apply(lambda x: 'Single' if x == 1 else 'Double' if x == 2 else 'Group')
        df_ppl.columns = ['Number of Booking', 'Room Type', 'Number of Adult', 'People Type']
        tmp1_ppl = group_dataframe(df_ppl, 'People Type', 'Number of Booking')
        tmp1_ppl.loc[tmp1_ppl.shape[0]] = tmp1_ppl.sum()
        tmp1_ppl.iloc[-1, 0] = 'Grand Total'

        tmp2_ppl = group_dataframe(df_ppl, ['People Type', 'Room Type'], 'Number of Booking')
        pivot_table = pd.pivot_table(
            data=tmp2_ppl,
            values='Number of Booking',
            index='Room Type',
            columns='People Type',
            fill_value=0,
            sort=True
        )
        display_download(tmp1_ppl, 'Customer')
        display_download(pivot_table, 'Customer and Room Type', False, True)

        # --------------------------------------------Time-------------------------------------------- #
        st.divider()
        st.subheader(analysis_list[3])
        booking_cols = st.columns((1, 1))
        arrival_cols = st.columns((1, 1))

        df_when = data[['Booking No', 'Booking Date', 'Arrival Date']].copy()
        df_when['Booking Day'] = df_when['Booking Date'].apply(lambda x: x.strftime('%A'))
        df_when['Arrival Day'] = df_when['Arrival Date'].apply(lambda x: x.strftime('%A'))
        df_when['Booking WDay'] = df_when['Booking Day'].apply(lambda x: 'Weekday' if x != 'Saturday' and x != 'Sunday' else 'Weekend')
        df_when['Arrival WDay'] = df_when['Arrival Day'].apply(lambda x: 'Weekday' if x != 'Saturday' and x != 'Sunday' else 'Weekend')
        df_when.columns = [
            'Number of Booking',
            'Booking Date',
            'Arrival Date',
            'Booking Day',
            'Arrival Day',
            'Booking WDay',
            'Arrival WDay'
        ]
        df_bookingd = group_dataframe(df_when, 'Booking Day', 'Number of Booking')
        df_bookingd.loc[df_bookingd.shape[0]] = df_bookingd.sum()
        df_bookingd.iloc[-1, 0] = 'Grand Total'

        df_bookingw = group_dataframe(df_when, 'Booking WDay', 'Number of Booking')
        df_bookingw.loc[df_bookingw.shape[0]] = df_bookingw.sum()
        df_bookingw.iloc[-1, 0] = 'Grand Total'

        df_arrivald = group_dataframe(df_when, 'Arrival Day', 'Number of Booking')
        df_arrivald.loc[df_arrivald.shape[0]] = df_arrivald.sum()
        df_arrivald.iloc[-1, 0] = 'Grand Total'

        df_arrivalw = group_dataframe(df_when, 'Arrival WDay', 'Number of Booking')
        df_arrivalw.loc[df_arrivalw.shape[0]] = df_arrivalw.sum()
        df_arrivalw.iloc[-1, 0] = 'Grand Total'

        with booking_cols[0]:
            display_download(df_bookingd, 'Booking Day')
        with booking_cols[1]:
            display_download(df_bookingw, 'Booking WDay')
        with arrival_cols[0]:
            display_download(df_arrivald, 'Arrival Day')
        with arrival_cols[1]:
            display_download(df_arrivalw, 'Arrival WDay')

        # --------------------------------------------Platform-------------------------------------------- #
        st.divider()
        st.subheader(analysis_list[4])
        df_platform = group_dataframe(data, 'Source', 'Booking No')
        df_platform.columns = ['Platform', 'Number of Booking']
        df_platform.loc[df_platform.shape[0]] = df_platform.sum()
        df_platform.iloc[-1, 0] = 'Grand Total'
        display_download(df_platform, 'Platform')

        # --------------------------------------------Nights-------------------------------------------- #
        st.divider()
        st.subheader(analysis_list[5])
        df_night = data[['Booking No', 'Total night(s)']].copy()
        df_night['Class'] = df_night['Total night(s)'].apply(lambda x: 'More than 1 night' if x > 1 else '1 night')
        df_night.columns = ['Number of Booking', 'Nights', 'Class']
        df_night = group_dataframe(df_night, 'Class', 'Number of Booking')
        df_night.loc[df_night.shape[0]] = df_night.sum()
        df_night.iloc[-1, 0] = 'Grand Total'
        display_download(df_night, 'Nights')

        # --------------------------------------------Races-------------------------------------------- #
        # st.divider()
        # st.subheader(analysis_list[6])
        # with open('races_prediction_model.pkl', 'rb') as f:
        #     vec, model = pickle.load(f)
        #
        # tmp_race = data[['Name ID', 'Contact Name']].copy()
        # name = tmp_race['Contact Name']
        # name = vec.transform(name)
        # races = model.predict(name)
        # tmp_race['predicted_race'] = races
        # tmp_race = tmp_race.drop('Contact Name', axis=1)
        # df_race = pd.merge(data, tmp_race, on='Name ID', how='left')
        # df_race = df_race.groupby('predicted_race') \
        #                  .agg({'Name ID': 'nunique', 'Booking No': 'nunique'}) \
        #                  .sort_values('Booking No', ascending=False) \
        #                  .reset_index()
        # df_race.columns = ['Predicted Race', 'Number of Guest', 'Number of Booking']
        # df_race.loc[df_race.shape[0]] = df_race.sum()
        # df_race.iloc[-1, 0] = 'Grand Total'
        # display_download(df_race, 'Races')


if __name__ == "__main__":
    run()
