#This is the summarize prompt used to extract room information from pdf:
Summarize_Prompt = """Please extract only the relevant information about rooms, including room details, configurations, prices, seasons, dates, and related data. Remove any unnecessary or unrelated content. Focus on the following fields:
- Room configurations (eg Queen bed, Queen bed & 2 x set of bunks, King / Queen, 2x Bunk Beds, 2 x Double Beds)
- Room name (eg Airlie Beach: Deluxe Bali Villa Cabin 1-2 people)
- Dates (season start and end)
- Prices (RRP adult cost)
- Supplier and property details
- Item-specific data
- Property adddress (this is where the room is located. eg 2634 Shute Harbour Rd  Jubilee Pocket  4802 Queensland Australia)
- Supplier name and address (this is the company that is providing the room, eg Discovery Parks at G'Day Group Holdings Level 7, 60 Light Square  Adelaide 5000 Australia )

Be concise and ensure that all extracted data is relevant to the room information."""




#This is the structured prompt which turns the summarization into a data table
Structured_Prompt = """Please return any information related to rooms or properties. 
Be verbose and very detailed. The more information related to properties/rooms the better.

Make sure for each property, if it is there, directly copy the text that includes data for the dates for peak and off peak season."""