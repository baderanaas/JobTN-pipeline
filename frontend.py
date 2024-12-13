import streamlit as st
import requests
import traceback

def main():
    st.title("📄 Resume Job Matcher")

    # File uploader
    uploaded_file = st.file_uploader(
        "Upload your resume (PDF)",
        type=["pdf"],
        help="Please upload your resume in PDF format",
    )

    if uploaded_file is not None:
        # Display file details
        file_details = {
            "Filename": uploaded_file.name,
            "File type": uploaded_file.type,
            "File size": f"{uploaded_file.size} bytes",
        }
        st.write("File Details:", file_details)

        # Submit button
        if st.button("Find Job Matches"):
            with st.spinner("Matching your resume to jobs..."):
                # Prepare files for upload
                files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}

                # Send request to FastAPI backend
                try:
                    # Use full URL with protocol
                    response = requests.post(
                        "http://127.0.0.1:8000/match-jobs/", 
                        files=files,
                        timeout=10  # Add a timeout
                    )

                    # Detailed status check
                    if response.status_code == 200:
                        job_matches = response.json()["job_matches"]

                        # Display results
                        st.subheader("🎯 Job Matches")
                        if job_matches:
                            for match in job_matches:
                                st.write(match)
                        else:
                            st.write("No job matches found.")
                    else:
                        st.error(f"Error matching jobs. Status code: {response.status_code}")
                        st.write(f"Response: {response.text}")

                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: {e}")
                    st.write(traceback.format_exc())  # Print full traceback
                except Exception as e:
                    st.error(f"Unexpected error: {e}")
                    st.write(traceback.format_exc())  # Print full traceback

if __name__ == "__main__":
    main()
