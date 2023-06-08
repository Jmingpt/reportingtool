import streamlit as st
import pandas as pd
import pickle


def displayNdownload(df, file_name='report', hide_index=True, file_index=False):
    st.dataframe(
        data=df,
        use_container_width=True,
        hide_index=hide_index,
    )

    encoded_data = df.to_csv(index=file_index).encode('utf-8')
    st.download_button(
        label='Download data as .csv',
        data=encoded_data,
        file_name=f'{file_name}.csv',
        mime='text/csv',
        key=f'{file_name.lower().replace(" ", "_")}_download'
    )


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

    if uploaded_file:
        st.divider()
        data = pd.read_excel(uploaded_file, skiprows=2).dropna(subset='Booking Date')
        data['Booking Date'] = data['Booking Date'].apply(lambda x: x[:-6])
        data['Booking Date'] = pd.to_datetime(data['Booking Date'])
        data['Arrival Date'] = pd.to_datetime(data['Arrival Date'])
        date_range = f"Date Range of dataset: " \
                     f"**_{min(data['Booking Date']).strftime('%Y-%m-%d')}_ - " \
                     f"_{max(data['Booking Date']).strftime('%Y-%m-%d')}_**"
        date_range_ph.markdown(date_range)
        data['Name ID'] = data['Contact Name'].apply(lambda x: x.lower().replace(' ', ''))
        data = data.drop(['Email', 'Phone No'], axis=1)
        data = data.astype(
            {
                "Booking No": "string"
            }
        )

        # ------------------------------------------Return------------------------------------------ #
        st.subheader('1. New vs returning customer')
        df_return = data[data['Status'] != 'Cancelled'].groupby('Name ID')['Booking No']\
                                                       .nunique()\
                                                       .sort_values(ascending=False)\
                                                       .reset_index()
        df_return['Status'] = df_return['Booking No'].apply(lambda x: 'Return' if x > 1 else 'First-time')
        df_return = df_return.groupby('Status')['Name ID']\
                             .count()\
                             .reset_index()
        df_return.loc[df_return.shape[0]] = df_return.sum()
        df_return.iloc[-1, 0] = 'Grand Total'
        df_return.columns = ['Status', 'Number of Guest']
        displayNdownload(df_return, 'Return Status')
        st.divider()

        # ------------------------------------------Room Type------------------------------------------ #
        st.subheader('2. Which type of room booked the most?')
        df_room = data[data['Status'] != 'Cancelled'].groupby('Room Type')['Booking No']\
                                                     .nunique()\
                                                     .sort_values(ascending=False)\
                                                     .reset_index()
        df_room.loc[df_room.shape[0]] = df_room.sum()
        df_room.iloc[-1, 0] = 'Grand Total'
        df_room.columns = ['Room Type', 'Number of Booking']
        displayNdownload(df_room, 'Room Type')
        st.divider()

        # ------------------------------------------People------------------------------------------ #
        st.subheader('3. What type of people booked the room?')
        df_ppl = data[data['Status'] != 'Cancelled'][['Booking No', 'Room Type', 'NoAdult']].copy()
        df_ppl['People Type'] = df_ppl['NoAdult'].apply(lambda x: 'Single' if x == 1 else 'Double' if x == 2 else 'Group')
        df_ppl.columns = ['Number of Booking', 'Room Type', 'Number of Adult', 'People Type']

        tmp1_ppl = df_ppl.groupby('People Type')['Number of Booking']\
                         .nunique()\
                         .sort_values(ascending=False)\
                         .reset_index()
        tmp1_ppl.loc[tmp1_ppl.shape[0]] = tmp1_ppl.sum()
        tmp1_ppl.iloc[-1, 0] = 'Grand Total'

        tmp2_ppl = df_ppl.groupby(['People Type', 'Room Type'])['Number of Booking']\
                         .nunique()\
                         .sort_values(ascending=False)\
                         .reset_index()

        pivot_table = pd.pivot_table(
            data=tmp2_ppl,
            values='Number of Booking',
            index='Room Type',
            columns='People Type',
            fill_value=0,
            sort=True
        )

        displayNdownload(tmp1_ppl, 'Customer')
        displayNdownload(pivot_table, 'Customer and Room Type', False, True)
        st.divider()

        # ------------------------------------------Time------------------------------------------ #
        st.subheader('4. When do they book the room?')
        df_when = data[data['Status'] != 'Cancelled'][['Booking No', 'Booking Date', 'Arrival Date']]
        df_when['Booking Day'] = df_when['Booking Date'].apply(lambda x: x.strftime('%A'))
        df_when['Arrival Day'] = df_when['Arrival Date'].apply(lambda x: x.strftime('%A'))
        df_when['Booking Week'] = df_when['Booking Day'].apply(lambda x: 'Weekday' if x != 'Saturday' and x != 'Sunday' else 'Weekend')
        df_when['Arrival Week'] = df_when['Arrival Day'].apply(lambda x: 'Weekday' if x != 'Saturday' and x != 'Sunday' else 'Weekend')
        df_when.columns = [
            'Number of Booking',
            'booking_date',
            'arrival_date',
            'booking_day',
            'arrival_day',
            'Booking Day',
            'Arrival Day'
        ]
        df_booking = df_when.groupby('Booking Day')['Number of Booking']\
                            .nunique()\
                            .sort_values(ascending=False)\
                            .reset_index()
        df_booking.loc[df_booking.shape[0]] = df_booking.sum()
        df_booking.iloc[-1, 0] = 'Grand Total'

        df_arrival = df_when.groupby('Arrival Day')['Number of Booking']\
                            .nunique()\
                            .sort_values(ascending=False)\
                            .reset_index()
        df_arrival.loc[df_arrival.shape[0]] = df_arrival.sum()
        df_arrival.iloc[-1, 0] = 'Grand Total'

        displayNdownload(df_booking, 'Booking Day')
        displayNdownload(df_arrival, 'Arrival Day')
        st.divider()

        # ------------------------------------------Platform------------------------------------------ #
        st.subheader('5. Where do they book?')
        df_platform = data[data['Status'] != 'Cancelled'].groupby('Source')['Booking No']\
                                                         .nunique()\
                                                         .sort_values(ascending=False)\
                                                         .reset_index()
        df_platform.loc[df_platform.shape[0]] = df_platform.sum()
        df_platform.iloc[-1, 0] = 'Grand Total'
        df_platform.columns = ['Platform', 'Number of Booking']
        displayNdownload(df_platform, 'Platform')
        st.divider()

        # ------------------------------------------Nights------------------------------------------ #
        st.subheader('6. How long do they stay?')
        df_night = data[data['Status'] != 'Cancelled'][['Booking No', 'Total night(s)']].copy()
        df_night['Class'] = df_night['Total night(s)'].apply(lambda x: 'More than 1 night' if x > 1 else '1 night')
        df_night.columns = ['Number of Booking', 'Nights', 'Class']
        df_night = df_night.groupby('Class')['Number of Booking']\
                           .nunique()\
                           .sort_values(ascending=False)\
                           .reset_index()
        df_night.loc[df_night.shape[0]] = df_night.sum()
        df_night.iloc[-1, 0] = 'Grand Total'
        displayNdownload(df_night, 'Nights')
        st.divider()

        # ------------------------------------------Races------------------------------------------ #
        st.subheader('7. Races Prediction (Additional)')
        with open('races_prediction_model.pkl', 'rb') as f:
            vec, model = pickle.load(f)

        tmp_race = data[data['Status'] != 'Cancelled'][['Name ID', 'Contact Name']]
        name = tmp_race['Contact Name']
        name = vec.transform(name)
        races = model.predict(name)
        tmp_race['predicted_race'] = races
        tmp_race = tmp_race.drop('Contact Name', axis=1)
        df_race = pd.merge(data, tmp_race, on='Name ID', how='left')
        df_race = df_race[df_race['Status'] != 'Cancelled'].groupby('predicted_race')\
                                                           .agg({'Name ID': 'nunique', 'Booking No': 'nunique'})\
                                                           .sort_values('Booking No', ascending=False)\
                                                           .reset_index()
        df_race.loc[df_race.shape[0]] = df_race.sum()
        df_race.iloc[-1, 0] = 'Grand Total'
        df_race.columns = ['Predicted Race', 'Number of Guest', 'Number of Booking']
        displayNdownload(df_race, 'Races')


if __name__ == "__main__":
    run()
