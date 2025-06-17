import streamlit as st
from PIL import Image
import piexif
import io
import zipfile

# --- Helper Functions ---
def deg_to_dms(deg):
    d = int(deg)
    m = int((deg - d) * 60)
    s = int(((deg - d) * 60 - m) * 60 * 100)
    return ((d, 1), (m, 1), (s, 100))

def add_exif_data(img, title, subject, tags, comments, gps_latitude, gps_longitude):
    exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

    exif_dict['0th'][piexif.ImageIFD.ImageDescription] = title.encode('utf-8')
    exif_dict['0th'][piexif.ImageIFD.XPSubject] = subject.encode('utf-16le')
    exif_dict['0th'][piexif.ImageIFD.XPKeywords] = tags.encode('utf-16le')
    exif_dict['0th'][piexif.ImageIFD.XPComment] = comments.encode('utf-16le')

    # Always set 5-Star Rating automatically
    rating_value = 99  # 5-star max for Windows
    exif_dict['0th'][18246] = rating_value

    # GPS Info
    if gps_latitude and gps_longitude:
        exif_dict['GPS'][piexif.GPSIFD.GPSLatitudeRef] = 'N' if gps_latitude >= 0 else 'S'
        exif_dict['GPS'][piexif.GPSIFD.GPSLatitude] = deg_to_dms(abs(gps_latitude))
        exif_dict['GPS'][piexif.GPSIFD.GPSLongitudeRef] = 'E' if gps_longitude >= 0 else 'W'
        exif_dict['GPS'][piexif.GPSIFD.GPSLongitude] = deg_to_dms(abs(gps_longitude))

    exif_bytes = piexif.dump(exif_dict)
    output = io.BytesIO()
    img.save(output, format='JPEG', exif=exif_bytes)
    return output

# --- Streamlit App ---
st.title("Bulk Image Optimizer")

# Step 1: Upload Images
uploaded_files = st.file_uploader(
    "",
    type=["jpg", "jpeg", "png", "webp", "bmp", "tiff", "heic"],
    accept_multiple_files=True
)

# Step 2: Metadata Inputs (Always visible now)
st.subheader("Set Metadata for All Images")
title = st.text_input("Title", "Default Title")
subject = st.text_input("Subject", "Default Subject")
tags = st.text_input("Tags (comma separated)", "tag1, tag2")
comments = st.text_input("Comments", "Default comment")
gps_latitude = st.number_input("GPS Latitude", value=23.6850)
gps_longitude = st.number_input("GPS Longitude", value=90.3563)

# Step 3: Process & Download Options
if uploaded_files:
    updated_images = []

    for uploaded_file in uploaded_files:
        image = Image.open(uploaded_file)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        updated_img = add_exif_data(
            image, title, subject, tags, comments, gps_latitude, gps_longitude
        )
        updated_filename = uploaded_file.name.rsplit('.', 1)[0] + ".jpg"
        updated_images.append((updated_filename, updated_img))

    # --- Option 1: Download All as ZIP ---
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for filename, img_bytes in updated_images:
            zip_file.writestr(filename, img_bytes.getvalue())
    zip_buffer.seek(0)
    st.download_button(
        label="⬇ Download All Images as ZIP",
        data=zip_buffer,
        file_name="updated_images.zip",
        mime="application/zip"
    )

    # --- Option 2: Download Images Individually ---
    st.markdown("### Or Download Images One by One:")
    for filename, img_bytes in updated_images:
        st.download_button(
            label=f"⬇ Download {filename}",
            data=img_bytes,
            file_name=filename,
            mime="image/jpeg"
        )
