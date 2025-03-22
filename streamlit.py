import streamlit as st
import requests
import base64

API_URL = "http://127.0.0.1:8080/api/v1/getcompanynews/"

st.title(" Company News Summary")

company_name = st.text_input("Enter Company Name:", "")

if st.button("Get News Summary"):
    if company_name:
        with st.spinner("Fetching news summary..."):
            try:
                response = requests.get(f"{API_URL}{company_name}")
                
                if response.status_code == 200:
                    data = response.json()

                    st.subheader(f" News Summary for {data['Company']}")

                    for article in data["Articles"]:
                        st.markdown(f"**Title:** {article['title']}")
                        st.write(f"**Summary:** {article['description']}")
                        st.write(f"**Sentiment:** {article['sentiment']} (Score: {article['score']})")
                        st.write(f"**Topics:** {', '.join(article['Topics'])}")
                        if article['link']:
                            st.write(f"**Link to full article:** [Click here]({article['link']})")
                        st.markdown("---")

                    if "Coverage Differences" in data and "Comparative Sentiment Score" in data["Coverage Differences"]:
                        if "Sentiment Distribution" in data["Coverage Differences"]["Comparative Sentiment Score"]:
                            st.subheader(" Sentiment Distribution")
                            st.json(data["Coverage Differences"]["Comparative Sentiment Score"]["Sentiment Distribution"])
                        else:
                            st.warning("Sentiment Distribution data not available.")
                        
                        if "Coverage Differences" in data["Coverage Differences"]["Comparative Sentiment Score"]:
                            st.subheader(" Coverage Differences")
                            for coverage in data["Coverage Differences"]["Comparative Sentiment Score"]["Coverage Differences"]:
                                st.write(f"**Comparison:** {coverage['Comparison']}")
                                st.write(f"**Impact:** {coverage['Impact']}")
                                st.markdown("---")
                        else:
                            st.warning("Coverage Differences data not available.")
                        
                        if "Topic Overlap" in data["Coverage Differences"]["Comparative Sentiment Score"]:
                            st.subheader(" Topic Overlap")
                            st.json(data["Coverage Differences"]["Comparative Sentiment Score"]["Topic Overlap"])
                        else:
                            st.warning("Topic Overlap data not available.")

                    st.subheader(" Final Sentiment Analysis")
                    st.write(data["Coverage Differences"].get("Final Sentiment Analysis", "No final sentiment data available."))


                    if "Audio" in data and data["Audio"]:
                        st.subheader(" News Summary Audio")  
                        audio_base64 = data["Audio"]
                        audio_bytes = base64.b64decode(audio_base64)
                        st.audio(audio_bytes, format="audio/mp3")
                else:
                    st.error("Failed to fetch data. Please try again.")
            except Exception as e:
                st.error(f"Error fetching data: {e}")
    else:
        st.warning("Please enter a company name.")
