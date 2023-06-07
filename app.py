import streamlit as st
import pandas as pd
import pickle


def download_csv(df, file_name, file_index=False):
    csv = df.to_csv(index=file_index).encode('utf-8')
    st.download_button(
        label="Download data as .csv",
        data=csv,
        file_name=f'{file_name}.csv',
        mime='text/csv',
    )


def run():
    st.set_page_config(
        page_title='Reporting Tool',
        page_icon=None,
        layout='centered',  # centered, wide
        initial_sidebar_state='auto',  # auto, expanded, collapsed
    )
    st.title('Springhill Report')

    uploaded_file = st.file_uploader(
        label='Select a file',
        type='xlsx',
        accept_multiple_files=False,
    )

    if uploaded_file:
        data = pd.read_excel(uploaded_file, skiprows=2).dropna(subset='Booking Date')
        data['Name ID'] = data['Contact Name'].apply(lambda x: x.lower().replace(' ', ''))
        data = data.astype(
            {
                "Booking No": "string",
                "Phone No": "string"
            }
        )

        # ----------------------------------Return---------------------------------- #
        st.subheader('1. New vs returning customer')
        df_return = data[data['Status'] != 'Cancelled'].groupby('Name ID')['Booking No'].nunique().sort_values(
            ascending=False).reset_index()
        df_return.columns = ['name_id', 'number_of_booking']
        df_return['status'] = df_return['number_of_booking'].apply(lambda x: 'Return' if x > 1 else 'First-time')
        df_return = df_return.groupby('status')['name_id'].count().reset_index()
        df_return.columns = ['status', 'number_of_customer']
        st.dataframe(
            data=df_return,
            use_container_width=True,
            hide_index=True,
        )
        download_csv(df_return, 'Return Status')

        # ----------------------------------Room Type---------------------------------- #
        st.subheader('2. Which type of room booked the most?')
        df_room = data[data['Status'] != 'Cancelled'].groupby('Room Type')['Booking No'].nunique().sort_values(ascending=False).reset_index()
        df_room.columns = ['room_type', 'number_of_booking']
        st.dataframe(
            data=df_room,
            use_container_width=True,
            hide_index=True,
        )
        download_csv(df_room, 'Room Type')

        # ----------------------------------People---------------------------------- #
        st.subheader('3. What type of people booked the room?')
        df_ppl = data[data['Status'] != 'Cancelled'][['Booking No', 'Room Type', 'NoAdult']].copy()
        df_ppl['label'] = df_ppl['NoAdult'].apply(lambda x: 'Single' if x == 1 else 'Double' if x == 2 else 'Group')
        df_ppl.columns = ['booking_id', 'room_type', 'number_of_adult', 'label']
        pivot_table = pd.pivot_table(
            df_ppl.groupby(['label', 'room_type'])['booking_id'].nunique().sort_values(ascending=False).reset_index(),
            values='booking_id',
            index='room_type',
            columns='label',
            fill_value=0,
            sort=True
        )
        st.dataframe(
            data=df_ppl.groupby('label')['booking_id'].nunique().sort_values(ascending=False).reset_index(),
            use_container_width=True,
            hide_index=True,
        )
        download_csv(df_ppl.groupby('label')['booking_id'].nunique().sort_values(ascending=False).reset_index(), 'Customer')
        st.dataframe(
            data=pivot_table,
            use_container_width=True,
            hide_index=False,
        )
        download_csv(pivot_table, 'Customer and Room Type', True)

        # ----------------------------------Time---------------------------------- #
        st.subheader('4. When do they book the room?')
        df_when = data[data['Status'] != 'Cancelled'][['Booking No', 'Booking Date', 'Arrival Date']]
        df_when['Booking Date'] = df_when['Booking Date'].apply(lambda x: x[:-6])
        df_when['Booking Date'] = pd.to_datetime(df_when['Booking Date'])
        df_when['Arrival Date'] = pd.to_datetime(df_when['Arrival Date'])
        df_when['Booking Day'] = df_when['Booking Date'].apply(lambda x: x.strftime('%A'))
        df_when['Arrival Day'] = df_when['Arrival Date'].apply(lambda x: x.strftime('%A'))
        df_when['Booking Week'] = df_when['Booking Day'].apply(lambda x: 'Weekday' if x != 'Saturday' and x != 'Sunday' else 'Weekend')
        df_when['Arrival Week'] = df_when['Arrival Day'].apply(lambda x: 'Weekday' if x != 'Saturday' and x != 'Sunday' else 'Weekend')
        df_when.columns = ['booking_id', 'booking_date', 'arrival_date', 'booking_day', 'arrival_day', 'booking_week', 'arrival_week']
        st.dataframe(
            data=df_when.groupby('booking_week')['booking_id'].nunique().sort_values(ascending=False).reset_index(),
            use_container_width=True,
            hide_index=True,
        )
        download_csv(df_when.groupby('booking_week')['booking_id'].nunique().sort_values(ascending=False).reset_index(), 'Booking Time')
        st.dataframe(
            data=df_when.groupby('arrival_week')['booking_id'].nunique().sort_values(ascending=False).reset_index(),
            use_container_width=True,
            hide_index=True,
        )
        download_csv(df_when.groupby('arrival_week')['booking_id'].nunique().sort_values(ascending=False).reset_index(), 'Arrival Time')

        # ----------------------------------Platform---------------------------------- #
        st.subheader('5. Where do they book?')
        df_platform = data[data['Status'] != 'Cancelled'].groupby('Source')['Booking No'].nunique().sort_values(ascending=False).reset_index()
        df_platform.columns = ['platform', 'number_of_booking']
        st.dataframe(
            data=df_platform,
            use_container_width=True,
            hide_index=True,
        )
        download_csv(df_platform, 'Platform')

        # ----------------------------------Nights---------------------------------- #
        st.subheader('6. How long do they stay?')
        df_night = data[data['Status'] != 'Cancelled'][['Booking No', 'Total night(s)']].copy()
        df_night['label'] = df_night['Total night(s)'].apply(lambda x: 'More than 1 night' if x > 1 else '1 night')
        df_night.columns = ['booking_id', 'nights', 'label']
        df_night = df_night.groupby('label')['booking_id'].nunique().sort_values(ascending=False).reset_index()
        st.dataframe(
            data=df_night,
            use_container_width=True,
            hide_index=True,
        )
        download_csv(df_night, 'Nights')

        # ----------------------------------Races---------------------------------- #
        st.subheader('7. Races Prediction (Additional)')
        with open('races_prediction_model.pkl', 'rb') as f:
            vec, model = pickle.load(f)

        df_race = data[data['Status'] != 'Cancelled'][['Name ID', 'Contact Name']]
        name = df_race['Contact Name']
        name = vec.transform(name)
        races = model.predict(name)
        df_race['predicted_race'] = races
        df_race = df_race.drop('Contact Name', axis=1)
        df = pd.merge(data, df_race, on='Name ID', how='left')
        df = df[df['Status'] != 'Cancelled'].groupby('predicted_race')['Booking No'].nunique().sort_values(ascending=False).reset_index()
        df.columns = ['predicted_race', 'number_of_booking']
        st.dataframe(
            data=df,
            use_container_width=True,
            hide_index=True,
        )
        download_csv(df, 'Races')


if __name__ == "__main__":
    run()
