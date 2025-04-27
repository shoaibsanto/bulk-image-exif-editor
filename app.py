import streamlit as st
from PIL import Image
import piexif
import io
import zipfile

# --- Helper Functions ---
def add_exif_data(img, title, subject, rating, tags, comments, gps_latitude, gps_longitude):
    exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

    exif_dict['0th'][piexif.ImageIFD.ImageDescription] = title.encode('utf-8')
    exif_dict['0th'][piexif.ImageIFD.XPSubject] = subject.encode('utf-16le')
    exif_dict['0th'][piexif.ImageIFD.XPKeywords] = tags.encode('utf-16le')
    exif_dict['0th'][piexif.ImageIFD.XPComment] = comments.encode('utf-16le')

    # Correct Rating Mapping
    rating_mapping = {
        0: 0,
        1: 12,
        2: 37,
        3: 62,
        4: 87,
        5: 99
    }
    rating_value = rating_mapping.get(rating, 0)
    exif_dict['0th'][18246] = rating_value  # Windows rating tag

    if gps_latitude and gps_longitude:
        exif_dict['GPS'][piexif.GPSIFD.GPSLatitudeRef] = 'N' if gps_latitude >= 0 else 'S'
        exif_dict['GPS'][piexif.GPSIFD.GPSLatitude] = deg_to_dms(abs(gps_latitude))
        exif_dict['GPS'][piexif.GPSIFD.GPSLongitudeRef] = 'E' if gps_longitude >= 0 else 'W'
        exif_dict['GPS'][piexif.GPSIFD.GPSLongitude] = deg_to_dms(abs(gps_longitude))

    exif_bytes = piexif.dump(exif_dict)
    output = io.BytesIO()
    img.save(output, format='JPEG', exif=exif_bytes)
    return output

def deg_to_dms(deg):
    d = int(deg)
    m = int((deg - d) * 60)
    s = int(((deg - d) * 60 - m) * 60 * 100)
    return ((d, 1), (m, 1), (s, 100))

# --- Streamlit App ---
st.title("Bulk Image EXIF Data Optimizer")

uploaded_files = st.file_uploader("Upload Images", type=["jpg", "jpeg", "png", "webp", "bmp", "tiff", "heic"], accept_multiple_files=True)

if uploaded_files:
    with st.expander("Set Metadata for All Images"):
        title = st.text_input("Title", "Default Title")
        subject = st.text_input("Subject", "Default Subject")
        rating = st.slider("Rating", 0, 5, 5)
        tags = st.text_input("Tags (comma separated)", "tag1, tag2")
        comments = st.text_input("Comments", "Default comment")
        gps_latitude = st.number_input("GPS Latitude", value=23.6850)
        gps_longitude = st.number_input("GPS Longitude", value=90.3563)
    
    if st.button("Apply Metadata and Download ZIP"):
        # Create a ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for uploaded_file in uploaded_files:
                image = Image.open(uploaded_file)

                # Convert non-JPEG images
                if image.mode in ("RGBA", "P"):
                    image = image.convert("RGB")

                updated_img = add_exif_data(image, title, subject, rating, tags, comments, gps_latitude, gps_longitude)
                updated_filename = uploaded_file.name.rsplit('.', 1)[0] + ".jpg"

                zip_file.writestr(updated_filename, updated_img.getvalue())

        zip_buffer.seek(0)

        # One download button for the zip
        st.download_button(
            label="Download All Images as ZIP",
            data=zip_buffer,
            file_name="updated_images.zip",
            mime="application/zip"
        )
