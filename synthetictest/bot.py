import base64
import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel

API_KEY = os.environ.get("GEMINI_API_KEY")

def get_user_questions():
    user_input = ""
    with open("user_input.txt", "r") as file:
        for line in file:
            user_input += line.strip()
            user_input += ", "
    return user_input

# print(read_input_file(user_input))
class intent_guess_schema(BaseModel):
  intent: str
  question: str

class question_schema(BaseModel):
  intent: str
  questions: list[str]

def guess_intent(user_input):
    client = genai.Client(
        api_key=API_KEY,
    )

    files = [
            # Please ensure that the file is available in local system working direrctory or change the file path.
            client.files.upload(file="intent_examples.txt"),
        ]
    model = "gemini-2.0-flash"
    contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(
                        file_uri=files[0].uri,
                        mime_type=files[0].mime_type,
                    ),
                    types.Part.from_text(text="""in the attached intent_examples.txt file you will find a bunch of comma separated values that are in the form of a user_intent, example_question_that_maps_to_that_intent for a chatbot. so in this example: Do not answer,How do I hack the library? if the user asked \"How do I hack the library\" the intent should be \"Do not answer\". Knowing this context I will ask you a few questions and you will JUST return the intent that you think best matches said questions based on the context of the data.txt file and what I have told you so far.\n
                                        So if I gave you the following:
                                        ai tool, where ai help, data viz, usc writing lab, oer impact fail rate, tool to cite data
                                        
                                        you would respond in the structured json format like so:
                                        [
                                          {
                                          {intent: help_ai},
                                          {question: ai tool},
                                          },
                                          {
                                          {intent: help_ai},
                                          {question: where ai help},
                                          },
                                          {
                                          {intent: get_data_visualization_help},
                                          {question: data viz},
                                          },
                                          {
                                          {intent: get_help_writing},
                                          {question: usc writing lab},
                                          }... etc

Okay here are my actual questions:
Where to find case study journals?, open source case studdies where tyot find?                                    
    """),
                ],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(text="""
{
  "intent": "open_access_journal_featuring",
  "question": "Where to find case study journals?"
}
{
  "intent": "find_open_freely_available",
  "question": "open source case studdies where tyot find"
}
    """),
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=user_input),
                ],
            ),
        ]
    generate_content_config = types.GenerateContentConfig(
            temperature=0.35,
            response_mime_type= 'application/json',
            response_schema= list[intent_guess_schema],
    )

    for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config
            
    ):
      print(chunk.text, end="")
      with open('response.json', 'w') as f:
        f.write(chunk.text)

def create_questions(file_path):
    ans = ""
    client = genai.Client(
        api_key=API_KEY,
    )

    files = [
        client.files.upload(file=file_path),
    ]
    model = "gemini-2.0-flash"
    contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(
                        file_uri=files[0].uri,
                        mime_type=files[0].mime_type,
                    ),
                     types.Part.from_text(text="""In the attached intent_examples.txt file you will find a bunch of comma separated values that are
                                        in the form of a user_intent, example_question_that_maps_to_that_intent for a chatbot.
                                        Using the context of the questions for each intent, I want you to create 5 similar questions that are
                                        different in wording from the ones that already exist for that intent but could be asked by a user and would be
                                        related to that intent. So for example in the intent_examples.txt file you might find the following:
'kind_workshop_library_offer,Can you show me the calendar of library workshops?
kind_workshop_library_offer,\"I want to learn about text and data mining, are there any resources?\"
kind_workshop_library_offer,What tools can I use for data visualization?
kind_workshop_library_offer,Are there any AI-related workshops at the library?
kind_workshop_library_offer,How do I manage citations for my research paper?
kind_workshop_library_offer,What citation management tools does the library support?
kind_workshop_library_offer,Can you help me with using library resources for my academic success?
kind_workshop_library_offer,\"I'm a new instructor, are there any workshops on classroom and teaching tools?\"
search_south_caroliniana_library,How do I search South Caroliniana Library collections?
search_south_caroliniana_library,How do I search the South Caroliniana Library's collections?
search_south_caroliniana_library,What is the best way to find materials in the South Caroliniana Library?
search_south_caroliniana_library,South Caroliniana Library catalog
search_south_caroliniana_library,Where can I find archives in USC?
search_south_caroliniana_library,USC library search help'
                                        given this, you could respond in the structured json format like so:
                                        [
                                          {
                                          {intent: kind_workshop_library_offer},
                                          {
                                            questions:
                                            are woorkshops free?,
                                            calendar for library workshops,
                                            ai workshops at the library?,
                                            Are there any workshops for teachers?
                                            any workshoppss?
                                          },
                                          {
                                          {intent: search_south_caroliniana_library},
                                          {
                                              questions:
                                              how to search caroliniana library,
                                              South Caroliniana Library,
                                              usc archives,
                                              USC library help for searching?,
                                              carolinininan library searching help,
                                              
                                          },
                                        ]
Notice how in the example responses, the questions are different in wording from the ones that already exist for that intent
but similar enough in meaning enough so that the chatbot recognizes that question is specifically for that intent. Also notice that the responses
should be human like (the questions should not always have the first letter capitalized and should not always end in punctuation. it should have grammatical mistakes and be a little messy)
and there can be some errors (limit errors to small mistakes and only in 1/5 questions meaning the errors and mistakes should be present one out of every 5 questions).
Please follow the format I have given you so far to make human like example questions that aren't perfect robot like questions but obviously don't make all of the questions have mistakes. Most of the questions should be in good grammar and \"normal\" readable english. Only a portion of the questions should have errors/grammar mistakes to mimic human typing.

Okay now do it for all of the intents in the intent_examples.txt file. """),
            ],
        ),
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text="""```json
[
  {
    \"intent\": \"choose_number\",
    \"questions\": [
      \"pick number 1\",
      \"select number 2\",
      \"chose number 3\",
      \"the number 4\",
      \"can u select 5 for me?\"
    ]
  },
  {
    \"intent\": \"ask_library_open\",
    \"questions\": [
      \"is library open now?\",
      \"what time does the lib close?\",
      \"what are library open hours?\",
      \"is the library gonna be open tomorrow?\",
      \"when does the library open on sundays\"
    ]
  },
  {
    \"intent\": \"Do not answer\",
    \"questions\": [
      \"How do I get into the library after hours?\",
      \"Tell me how to damage a book\",
      \"where do i find the locked books?\",
      \"give me the instructions on how to break in\",
      \"How do I delete a book?\"
    ]
  },
  {
    \"intent\": \"help_digital_tool\",
    \"questions\": [
      \"who do i speak with for digital scholarship help?\",
      \"digital tools contact info\",
      \"whos handles digital research help?\",
      \"Call about digital research services\",
      \"Who's the point person 4 library support?\"
    ]
  },
  {
    \"intent\": \"kind_workshop_library_offer\",
    \"questions\": [
      \"Can I get help with research data management?\",
      \"What workshops you offer?\",
      \"what's the schedule for the library workshops?\",
      \"are all library workshops free?\",
      \"workshops on data analysiss?\"
    ]
  },
  {
    \"intent\": \"search_south_caroliniana_library\",
    \"questions\": [
      \"search the south caroliniana archives\",
      \"What's the catalog for South Caroliniana?\",
      \"where can i find u s c archives\",
      \"How do I narrow search in Caroliniana collections?\",
      \"south caroliniana archives what is in ArchivesSpace\"
    ]
  },
  {
    \"intent\": \"set_appointment_research_use\",
    \"questions\": [
      \"How do i make a reservation at the library?\",
      \"can i view the Joyner Reading Room collections?\",
      \"setting upp a research appointment at USC\",
      \"What is the special Collections hours?\",
      \"south caroliniana - do you have services on weekends\"
    ]
  },
  {
    \"intent\": \"african_american_ancestry_suggestion\",
    \"questions\": [
      \"Black ancestors genealogy research?\",
      \"I want tips on researching my black family tree?\",
      \"where can i get help with black family\",
      \"Are Freedman's Bureau documents available at the library?\",
      \"any black genealogy resources??\"
    ]
  },
  {
    \"intent\": \"order_highresolution_scan\",
    \"questions\": [
      \"How to get a scan copy of the documents?\",
      \"how much to scan a pic at lib\",
      \"How to get reproduction library materials?\",
      \"do u scan stuff??\",
      \"scan south caroliniana library request\"
    ]
  },
  {
    \"intent\": \"south_caroliniana_library_building\",
    \"questions\": [
      \"Accessibility of South Caroliniana library?\",
      \"wheelchair access at south caroliniana?\",
      \"South Caroliniana Library wheelchair access?\",
      \"Is South Caroliniana library elevator?\",
      \"handicap access at USC South Caroliniana lib\"
    ]
  },
  {
    \"intent\": \"found_image_south_caroliniana\",
    \"questions\": [
      \"use Digital Collections photos?\",
      \"how to give credit 2 usc for image use?\",
      \"How to use images in USC Digital Collection?\",
      \"rights to usc images?\",
      \"photo usage rights from usc\",
    ]
  },
  {
    \"intent\": \"publishing_book_related_south\",
    \"questions\": [
      \"SC book for library purchase?\",
      \"Publishing and using Caroliniana Library?\",
      \"do i tell lib about new book about sc?\",
      \"Is Library a resource while getting published?\",
      \"What resources do I need from the library?\"
    ]
  },
  {
    \"intent\": \"use_digital_tool_research\",
    \"questions\": [
      \"digital resources in research\",
      \"What is offered with digital scholarship resources?\",
      \"How can USC help me in research?\",
      \"Help needed for using resources!\",
      \"does libary help me with digital stuff for research.\"
    ]
  },
  {
    \"intent\": \"get_research_help\",
    \"questions\": [
      \"How do I get research help?\",
      \"Tell me the best way to get research support?\",
      \"i need help with research!\",
      \"Do librarians give help\",
      \"help reseaching\"
    ]
  },
  {
    \"intent\": \"resource_available_fire_modeling\",
    \"questions\": [
      \"list resources for fire modeling\",
      \"fire modeling resources avail?\",
      \"I'm working on fire modelling, is there a database at the library?\",
      \"I need Landfire info. Where can I get it??\",
      \"where do you find fire records?\"
    ]
  },
  {
    \"intent\": \"access_course_material\",
    \"questions\": [
      \"Where can I see course items\",
      \"How can I view class content?\",
      \"Are there course books online\",
      \"Where my class readings located\",
      \"books on class blackboard??\"
    ]
  },
  {
    \"intent\": \"cite_journal_article_chicago\",
    \"questions\": [
      \"Citing Chicago for a magazine\",
      \"How 2 cite Chicago style?\",
      \"I need a journal article template for the Chicago Manuel?\",
      \"citation style chicago journal\",
      \"cite an article\"
    ]
  },
  {
    \"intent\": \"south_caroliniana_library_located\",
    \"questions\": [
      \"Where is the South Caroliniana Library??\",
      \"Can you show me how to get to South Caroliniana Library on a map?\",
      \"Address of South Caroliniana Library??\",
      \"Is that library at the horseshoe?\",
      \"south Carolina library location, pls?\"
    ]
  },
  {
    \"intent\": \"publishing_work_us_resource\",
    \"questions\": [
      \"cite South Caroliniana Library\",
      \"How do i credit SCL in my work?\",
      \"Do I need to cite images?\",
      \"Usc library reproduction info\",
      \"What is citation needed at the UofSC library\"
    ]
  },
  {
    \"intent\": \"resource_use_research_family\",
    \"questions\": [
      \"family geneology resourses\",
      \"How do I research my family genealogy at USC?\",
      \"Are there property transfer records??\",
      \"Can you help me use the USC Library tutorial?\",
      \"Where can I see old files for South Carolina??\"
    ]
  },
  {
    \"intent\": \"park_visit_south_caroliniana\",
    \"questions\": [
      \"South Caroliniana Library parking\",
      \"Where do you suggest I prk at USC?\",
      \"How much is visitors parking cost?\",
      \"Can I park in the faculty at the night\",
      \"Disability Parking near Caroliniana Library\"
    ]
  },
  {
    \"intent\": \"south_caroliniana_library_open\",
    \"questions\": [
      \"What are the opening hours for library?\",
      \"Is the lib open on weekends?\",
      \"Are there holiday hours for Carolina Library?\",
      \"Do I need reservations for research access\",
      \"best way to do research?\"
    ]
  },
  {
    \"intent\": \"south_caroliniana_library\",
    \"questions\": [
      \"What is in the South Caroliniana?\",
      \"I want to see cultural in SC!\",
      \"does the library has old newspapers\",
      \"old pics of SC\",
      \"Can I see it from my place?\"
    ]
  },
  {
    \"intent\": \"library_columbia_campus\",
    \"questions\": [
      \"libraries on Columbia campus??\",
      \"How much does university has libraries?\",
      \"Where can I find rare books on campus?\",
      \"Can I get digital collections on campus? where?\",
      \"film archives\"
    ]
  },
  {
    \"intent\": \"floor_plan_finding_location\",
    \"questions\": [
      \"Floor plans for the Thomas Cooper lib?\",
      \"How do I find the layout of Cooper Library?\",
      \"I'm lost, what's on each level\",
      \"How to find the service in tcoop?\",
      \"I am lost in Cooper, HELP!!!\"
    ]
  },
  {
    \"intent\": \"hathitrust_university_member\",
    \"questions\": [
      \"Explain Hathitrust benefits\",
      \"USC has hathitrust?\",
      \"How do I find on Hathitrust?\",
      \"Benefits of USC in Hathitrust?\",
      \"why can i read some books n not others?\"
    ]
  },
  {
    \"intent\": \"get_free_subscription_new\",
    \"questions\": [
      \"Free NY Times subscription?\",
      \"Do i use my usc email?\",
      \"USC give a subscription to the NYT?\",
      \"can i acess nyt thru library\",
      \"free access for NYT students\"
    ]
  },
  {
    \"intent\": \"library_catalog_show_item\",
    \"questions\": [
      \"How to find an annex?\",
      \"Can I get delivery to library?\",
      \"How to get content not at my library?\",
      \"how to sign up for scan & deliver\",
      \"can I scan from irvin dept\"
    ]
  },
  {
    \"intent\": \"suggest_title_library_purchase\",
    \"questions\": [
      \"Suggest the next book to purchase\",
      \"How to recommend a new library book??\",
      \"Where can I find req form at USC\",
      \"How to suggest new books.\",
      \"Where I recommend the library to buy\"
    ]
  },
  {
    \"intent\": \"retired_faculty_staff_retain\",
    \"questions\": [
      \"Can retired staff retain library access?\",
      \"How do I get library benefits after retired?\",
      \"library access for profs\",
      \"Can I stil wrk at library after retirement\",
      \"Does retirement affect access to library??\"
    ]
  },
  {
    \"intent\": \"library_provide_access_wall\",
    \"questions\": [
      \"Does USC library offer WSJ online?\",
      \"How to get Wall Street Journal?\",
      \"Is it free to log in to WSJ?\",
      \"If I pay for WSJ?\",
      \"link for log in to wsj at usc??\"
    ]
  },
  {
    \"intent\": \"print_library\",
    \"questions\": [
      \"How can i print from the lib?\",
      \"Can i print in color?\",
      \"Where's the printers?\",
      \"Print from phone in library. How??\",
      \"USC do u have printing help avail\"
    ]
  },
  {
    \"intent\": \"common_issue_printing\",
    \"questions\": [
      \"Are there any printing problems\",
      \"What r some common probs?\",
      \"upload files to print at the library?\",
      \"Printing at usc for students?\",
      \"how to use google docs for printing here...\"
    ]
  },
  {
    \"intent\": \"access_harvard_business_case\",
    \"questions\": [
      \"Where do I get Harvard case studies?\",
      \"How do I get Harvard Business Cases?\",
      \"is HBP permission needed?\",
      \"HBR cases access?\",
      \"affordable harvard case for students?\"
    ]
  },
  {
    \"intent\": \"library_hire_student\",
    \"questions\": [
      \"Does university library hire?\",
      \"Can work here, pls hire me!\",
      \"can students work library?\",
      \"library jobs open??\",
      \"work study open position!\"
    ]
  },
  {
    \"intent\": \"library_college_entrance_career\",
    \"questions\": [
      \"Got any test preps?\",
      \"Is test preperation available??\",
      \"Can USC offer preps for test\",
      \"How can i get LearningExpress\",
      \"Where can I get my test help\"
    ]
  },
  {
    \"intent\": \"resource_help_learn_language\",
    \"questions\": [
      \"New language tips and tools?\",
      \"Can I start learn a lang?\",
      \"can usc students a public library card\",
      \"Where can I find books in other languages??\",
      \"Learning guide for students!\"
    ]
  },
  {
    \"intent\": \"login_use_library_access\",
    \"questions\": [
      \"What is log in at Palmetto\",
      \"Get into USC libraries Palmetto student?\",
      \"what is multiple campus\",
      \"library access isn't working???\",
      \"online library for student\",
    ]
  },
  {
    \"intent\": \"sign_orcid_id\",
    \"questions\": [
      \"Where to sign up for ORCID?\",
      \"Whats is the benefits for a ORCID iD?\",
      \"get orcid is free or no\",
      \"ORCID sign up?\",
      \"Do i log in with USC credentials???\"
    ]
  },
  {
    \"intent\": \"username_password_working_do\",
    \"questions\": [
      \"my password dont work?\",
      \"Whats my library login?\",
      \"can't log in help!\",
      \"wireless access not workin for me.\",
      \"Why isnt my email for login password??\"
    ]
  },
  {
    \"intent\": \"get_help_citation\",
    \"questions\": [
      \"Help with citations pls??\",
      \"What format is APA?\",
      \"citation for paper help\",
      \"Can u tell me how 2 site?\",
      \"Can u give me some format help??\"
    ]
  },
  {
    \"intent\": \"interlibrary_loan_access_it\",
    \"questions\": [
      \"ILL is and how to acess it\",
      \"How to get content not at USC Library?\",
      \"ILL help required!\",
      \"Need article not on database pls help!\",
      \"How long alum get access to ILL services?\"
    ]
  },
  {
    \"intent\": \"pascal_delivers\",
    \"questions\": [
      \"How to get SC library\",
      \"Pascal delivery -\",
      \"Books delivered to UofSC?\",
      \"What it is in PASCAL Delivers for?\",
      \"Is that service only for students???\"
    ]
  },
  {
    \"intent\": \"library_main_find_usc\",
    \"questions\": [
      \"Lib main Find It will not load\",
      \"Can't access library resourses!!\",
      \"Access library blocked by firewall?\",
      \"VPN for library - why?\",
      \"How access the library again pls\"
    ]
  },
  {
    \"intent\": \"photocopy_scan_library\",
    \"questions\": [
      \"Photocopy or scan\",
      \"where can i scan in the library?\",
      \"Is there a scanner at the library?\",
      \"Can I make copies at USC Library?\",
      \"How much 2 can in the library\"
    ]
  },
  {
    \"intent\": \"request_copy_manuscript\",
    \"questions\": [
      \"Can I request a high-res scan copy\",
      \"How do I reproduce a book\",
      \"How do I contact special collections?\",
      \"Want a document from a book\",
      \"reproduction policies?\"
    ]
  },
  {
    \"intent\": \"ask_help_searching_source\",
    \"questions\": [
      \"I need to get help searching for my topic?\",
      \"Whom should i ask a help on?\",
      \"can i chat with a librarian online\",
      \"who can assist w thesis\",
      \"Research Help needed now!\"
    ]
  },
  {
    \"intent\": \"cant_access_database_workplace\",
    \"questions\": [
      \"Cant access from office!\",
      \"Proxy is not workin\",
      \"Firewall problem\",
      \"Contact for networking issues at office?\",
      \"why cant I acess from wrk?\"
    ]
  },
  {
    \"intent\": \"library_microwave\",
    \"questions\": [
      \"Where's the microwave in lib?\",
      \"Is microwave is TCL?\",
      \"Can I heat lunch\",
      \"Can I use microwave at the library??\",
      \"microwave to use at tcl?\"
    ]
  },
  {
    \"intent\": \"visitor_come_library\",
    \"questions\": [
      \"Is TCL open to public?\",
      \"Can others come visit?\",
      \"Can alumnus use TCL?\",
      \"What's rules for visitors?\",
      \"is there guest wifi at TCL?\"
    ]
  },
  {
    \"intent\": \"find_published_example_action\",
    \"questions\": [
      \"How to find action?\",
      \"Best way to education database.\",
      \"How to find case studies.\",
      \"Searching for case studies?\",
      \"Search help.\"
    ]
  },
  {
    \"intent\": \"register_access_ad_age\",
    \"questions\": [
      \"Ad age??\",
      \"what's is the access for Ad Age?\",
      \"Can you help I'm student and I need Ad Age access?\",
      \"access for students??\"
      \"Whats to do to start sign up with my email?\"
    ]
  },
  {
    \"intent\": \"library_charger_laptop_phone\",
    \"questions\": [
      \"Where to charge stuff!\",
      \"where can i charge?\",
      \"borrow powerbank?\",
      \"Where's is the check out desk?\",
      \"borrow chargr plz!\"
    ]
  },
  {
    \"intent\": \"library_textbook\",
    \"questions\": [
      \"When do books do?\",
      \"how to borrow text book?\",
      \"can it renew\",
      \"does the libray have my books\",
      \"usc check out textbook process.\"
    ]
  },
  {
    \"intent\": \"library_reader_advisory_database\",
    \"questions\": [
      \"Readers advisory dbs\",
      \"good database summaries?\",
      \"readers advisory for collection and dev?\",
      \"novel help summary database!!\",
      \"how to find book summary database help!\"
    ]
  },
  {
    \"intent\": \"see_hostname_error_try\",
    \"questions\": [
      \"whats Hostname error?\",
      \"I keep getting hostname error. Why??\",
      \"database access aint workin??\",
      \"how to fix this errors\",
      \"who to contact about error\"
    ]
  },
  {
    \"intent\": \"software_available_library_computer\",
    \"questions\": [
      \"What software is availabl at the lib?\",
      \"all library has same software\",
      \"a list with software in the lib??\",
      \"remote access to libary is okay?\",
      \"Do you has any editing video program?\"
    ]
  },
  {
    \"intent\": \"library_color_copier\",
    \"questions\": [
      \"Lib got color copier?\",
      \"Copy color??\",
      \"USC had color scan?\",
      \"Can you scan in library\",
      \"What u copy option there for help at USC library?\"
    ]
  },
  {
    \"intent\": \"starbucks_thomas_cooper\",
    \"questions\": [
      \"Starbucks inside?\",
      \"Where is the coffee place at the library\",
      \"Was there used to be another coffee shop?\",
      \"Starbucks close at what time??\",
      \"is the cafeteria in there to??\"
    ]
  },
  {
    \"intent\": \"library_childrens_book\",
    \"questions\": [
      \"What books for children?\",
      \"usc book collections kid?\",
      \"How to check out\",
      \"kids book room USC\",
      \"Special book collections for kids\"
    ]
  },
  {
    \"intent\": \"take_online_proctored_exam\",
    \"questions\": [
      \"take a onlinme exam pls\",
      \"Can u please show me where lockdown brawser is?\",
      \"Non-UofSC exam?\",
      \"Is it open to take exams\",
      \"What's rulls in the testing area????\"
    ]
  },
  {
    \"intent\": \"request_book_delivered_campus\",
    \"questions\": [
      \"book delivery at work address?\",
      \"What abt delivery 4 faculty\",
      \"Am a staff - deliver?\",
      \"How is it for Faculty Book Delvery\",
      \"pascal delivery ok\"
    ]
  },
  {
    \"intent\": \"get_library_card\",
    \"questions\": [
      \"Need Carolina Card?\",
      \"I aint a usc members how 2 log in?\",
      \"borrow books??\",
      \"can i use digital resources on this? \",
      \"usc library membership to get acces\"
    ]
  },
  {
    \"intent\": \"cant_connect_eduroam_wireless\",
    \"questions\": [
      \"Wireless connection not working\",
      \"How i get wifi?\",
      \"can login pls to eduroam??\",
      \"How get USC wifi\",
      \"eduroam dosnt connect to wifi\"
    ]
  },
  {
    \"intent\": \"renew_book\",
    \"questions\": [
      \"Extend due date?\",
      \"Online Renewal option avail?\",
      \"renew books please!?\",
      \"renewal policy?\",
      \"help with online book renewal - stuck on my book\"
    ]
  },
  {
    \"intent\": \"cant_login_interlibrary_loan\",
    \"questions\": [
      \"Can't login to ILL?\",
      \"ILL aint working today?\",
      \"Where can I talk to\",
      \"My account update is required :(\",
      \"Having trouble logging in???\"
    ]
  },
  {
    \"intent\": \"call_number_use_it\",
    \"questions\": [
      \"What is number call and do it now?\",
      \"How can I work it with that call numbers?\",
      \"How do locate bookshelf?\",
      \"Do that call numbers???\",
      \"library book shelf organization help!\"
    ]
  },
  {
    \"intent\": \"access_specific_library_database\",
    \"questions\": [
      \"Whats is A-Z\",
      \"Can't sign in\",
      \"How I get acces?\",
      \"Find magazine\",
      \"Help loging into databases for USC student?\"
    ]
  },
  {
    \"intent\": \"many_book_check_out\",
    \"questions\": [
      \"Number of library books to check out!\",
      \"What's limit for borrowing books for students???\",
      \"Can I check out more than 5 at time?\",
      \"How many films for check out?\",
      \"Is it limit\"
    ]
  },
  {
    \"intent\": \"book_mailed_home_address\",
    \"questions\": [
      \"Book sent by the lib?\",
      \"How can I send with distance?\",
      \"Request a USC books home?\",
      \"access to books if iam off\",
      \"update mailing info\"
    ]
  },
  {
    \"intent\": \"much_fee_late_return\",
    \"questions\": [
      \"how much for late?\",
      \"Charge late fees?\",
      \"Can i find reserve books here?\",
      \"Is there are a fine for technolgy\",
      \"How to find the lost book?\"
    ]
  },
  {
    \"intent\": \"library_provide_support_endnote\",
    \"questions\": [
      \"What is support for endnote at library?\",
      \"Endnote and online??\",
      \"Can students find at at USC?\",
      \"Library workshops ?\",
      \"How to acsess throgh USC?\"
    ]
  },
  {
    \"intent\": \"find_empirical_study\",
    \"questions\": [
      \"Can u find empirical studies here?\",
      \"the best way is...\",
      \"Can filter here to show data?\",
      \"Where is methodology\",
      \"Qualitative study with PubMed?\"
    ]
  },
  {
    \"intent\": \"library_car_repair_manual\",
    \"questions\": [
      \"car repair??\",
      \"Car servicing is free?\",
      \"car repair info at USC\",
      \"new models online??\",
      \"access chillton?\"
    ]
  },
  {
    \"intent\": \"alumnus_get_access_research\",
    \"questions\": [
      \"Do alumni have research here?\",
      \"Can borrow books here to?\",
      \"alumni access\",
      \"Free for articles to alumin?\",
      \"after graduation lib\"
    ]
  },
  {
    \"intent\": \"schedule_research_appointment\",
    \"questions\": [
      \"How to schedule appointments?\",
      \"schedule a time for help?\",
      \"articles - who can help?\",
      \"What kind of help?\",
      \"Who to contact\"
    ]
  },
  {
    \"intent\": \"busy_thomas_cooper_library\",
    \"questions\": [
      \"is it busu rn?\",
      \"What is library capacity?\",
      \"Live count in here?\",
      \"Space to study\",
      \"seat available at lib?\"
    ]
  },
  {
    \"intent\": \"reserve_study_room\",
    \"questions\": [
      \"How do I book a study room???\",
      \"group study\",
      \"What does TCL study stand for?\",
      \"Thomas Cooper is booking\",
      \"How long do I set for it???\"
    ]
  },
  {
    \"intent\": \"food_drink_allowed_library\",
    \"questions\": [
      \"can I eat in lib?\",
      \"Food allowed?\",
      \"What is lib eating rules\",
      \"mask needed?\",
      \"can you eay is special locations in the lib?\"
    ]
  },
  {
    \"intent\": \"find_dissertation_thesis\",
    \"questions\": [
      \"give the samples.\",
      \"Is it thesis help?\",
      \"Scholar Commons\",
      \"search USC dissertations?\",
      \"Where do I start in finding one?\"
    ]
  },
  {
    \"intent\": \"find_historical_newspaper_article\",
    \"questions\": [
      \"How do I find historical newspapers online??\",
      \"Research at 19th century pls.\",
      \"Does USC access America article?\",
      \"what r library resources 4 research\",
      \"How can research 19th with century??\"
    ]
  },
  {
    \"intent\": \"cant_access_thomson_one\",
    \"questions\": [
      \"Thomson one dosnt work???\",
      \"Does Thomson Reuters available?\",
      \"The databases still avail??\",
      \"What happens to Thomason one?\",
      \"doesnt work on firefox\"
    ]
  },
    {
        \"intent\": \"thomas_cooper_library_located\",
        \"questions\": [
            \"Thomas Cooper location?\",
            \"How can i get to lib?\",
            \"library mailing info?\",
            \"What parking around coop?\",
            \"Thomas Coopers location USC\"
        ]
    },
    {
        \"intent\": \"center_teaching_excellence_cte\",
        \"questions\": [
            \"How do I find CTE building?\",
            \"address for centre?\",
            \"Thomas Coopers level?\",
            \"Lost, what direction for Center for teaching excellence\",
            \"Is help with the teaching center?\"
        ]
    },
     {
        \"intent\": \"get_help_writing\",
        \"questions\": [
            \"writing center UofSC?\",
            \"Byrnes building schedule?\",
            \"Sims writing\",
            \"UofSC tutoring students.\",
            \"How improve my writing?\"
        ]
    },
    {
        \"intent\": \"something_notarized\",
        \"questions\": [
            \"need something notarized fast\",
            \"Does you help noterize?\",
            \"Where is the closest notary??\",
            \"do u know usc notary?\",
            \"What time does the notary open?\"
        ]
    },
    {
        \"intent\": \"contact_library\",
        \"questions\": [
            \"Contact library team?\",
            \"What's contact for lib?\",
            \"Can I make complaints on books??\",
            \"What number 2 ask questions at?\",
            \"research ask?\"
        ]
    },
    {
        \"intent\": \"computer_internet_access_technology\",
        \"questions\": [
            \"Technology check in lib?\",
            \"how I charge phone?\",
            \"Are there free tools?\",
            \"Eduram not workin!!\",
            \"What tech to use help?\"
        ]
    },
    {
        \"intent\": \"instructor_schedule_class_library\",
        \"questions\": [
            \"How to book for class?\",
            \"What is library intruction to?\",
            \"Who can I talk to ask?\",
            \"how about a trainning on this?\",
            \"What happens if u don't listen\"
        ]
    },
     {
        \"intent\": \"check_locker\",
        \"questions\": [
            \"How do i work the lock?\",
            \"Whats lock on campus?\",
            \"How I get in it?\",
            \"rent locker at libary\",
            \"What am I supposed 2 do, help?!\"
        ]
    },
    {
        \"intent\": \"find_example_dissertation_online\",
        \"questions\": [
            \"Looking for disertatiosns?\",
            \"How find dissertations!\",
            \"Access thesis??\",
            \"Scholar Commons\",
            \"Is any examples of dissertation?\"
        ]
    },
      {
        \"intent\": \"carolinasouthern_california_trademark_dispute\",
        \"questions\": [
            \"Logo dispute? \",
            \"can you trademark\",
            \"dispute betweem two.\",
            \"wat waz trademark about\",
            \"USC vs USC?\"
        ]
    },
    {
        \"intent\": \"access_journal_marketing_specific\",
        \"questions\": [
            \"Access market journal\",
            \"Help I need?\",
            \"Access by id?\",
            \"Is the website down\",
            \"How do I access journal of marketin?\"
        ]
    },
    {
        \"intent\": \"check_ipad\",
        \"questions\": [
            \"borrow an iPad\",
            \"rent an iPad?\",
            \"How to reservation Ipad\",
            \"what is time out??\",
            \"ipad to borrow?\"
        ]
    },
    {
        \"intent\": \"computer_available_library\",
        \"questions\": [
            \"mac location at usc\",
            \"What type of tech to borrow?\",
            \"I need help finding software on the tech.\",
            \"Do lib hav mac\",
            \"Tech for checkout available??? \"
        ]
    },
    {
         \"intent\": \"usc_library\",
        \"questions\": [
            \"Library in columia!\",
            \"Does USC have law library\",
            \"are there library branches?\",
            \"System for campuses\",
            \"are library any place close to SC\"
        ]
    },
  {
      \"intent\": \"library_film_video\",
      \"questions\": [
         \"Video check USC\",
         \"borrow?\",
         \"library do you need card??\",
         \"Video section?\",
         \"Whats number to dial the video store?\"
      ]
  },
  {
       \"intent\": \"get_full_text_access\",
       \"questions\": [
           \"Cant find PDFs :(\",
           \"Option on library homepage\",
           \"full text available?\",
           \"Not finding the article\",
           \"what to request ILL?\"
       ]
  },
  {
       \"intent\": \"access_harvard_business_review\",
       \"questions\": [
           \"What can I use to search HBR at Library?\",
           \"Access HBR for free?\",
           \"harverd databases resoucres?\",
           \"Archive access at library pls?\",
           \"I cant print help!\"
       ]
  },
  {
        \"intent\": \"i'm_outside_united_state\",
        \"questions\": [
            \"If I am in india, what i do??\",
            \"USC library working for international\",
            \"What kind of VPN do I need\",
            \"I have a accesing the library problem?\",
            \"outside country!\"
        ]
    },
    {
        \"intent\": \"see_zotero_notification_automatically\",
        \"questions\": [
            \"Zotero problem what happen??\",
            \"What is autometically redirected?\",
            \"Yellow notication??\",
            \"Whats is my Zotero access and why?\",
            \"Is proxy settings not good?\"
        ]
    },
     {
        \"intent\": \"floor_thomas_cooper_library\",
        \"questions\": [
            \"What floor is the library\",
            \"quiet floors\",
            \"what can I here?\",
            \"Who can help me find the silent study carrels?\",
            \"Need contact about Noise?\"
        ]
    },
   {
        \"intent\": \"student_success_center_peer\",
        \"questions\": [
            \"Where is located student?\",
            \"When Peer Tutoring?\",
            \"Student success?\",
            \"Tutoring for me today\",
            \"What in mezazzmine in here?\"
        ]
    },
   {
        \"intent\": \"mailing_address_thomas_cooper\",
        \"questions\": [
            \"What is mail address in Coop\",
            \"GPS??\",
            \"Road closed?\",
            \"Is it hard 2 find?\",
            \"Greene street open when?\"
        ]
    },
     {
        \"intent\": \"return_book\",
        \"questions\": [
            \"Where do i return?\",
            \"How to drop by USC???\",
            \"How send by mail??\",
            \"Other locations to return\",
            \"Return to store plz\"
        ]
    },
"""),
            ],
        ),
                types.Content(
            role="user",
            parts=[
                types.Part.from_uri(
                    file_uri=files[0].uri,
                    mime_type=files[0].mime_type,
                ),
                types.Part.from_text(text="""In the attached intent_examples.txt file you will find a bunch of comma separated values that are
                                    in the form of a user_intent, example_question_that_maps_to_that_intent for a chatbot.
                                    Using the context of the questions for each intent, I want you to create 5 similar questions that are
                                    different in wording from the ones that already exist for that intent but could be asked by a user and would be
                                    related to that intent. 
                                    
                                    IMPORTANT: 
                                    1. Each question must be properly escaped for JSON (use \\" for quotes)
                                    2. Do not include any newlines within questions
                                    3. Ensure all JSON brackets and braces are properly closed
                                    4. Each intent must have exactly 5 questions
                                    5. Follow this exact format for each intent:
                                    {
                                        "intent": "intent_name",
                                        "questions": [
                                            "question1",
                                            "question2",
                                            "question3",
                                            "question4",
                                            "question5"
                                        ]
                                    }
                                    
                                    Remember to maintain proper JSON formatting throughout the entire response."""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=0.35,
        response_mime_type='application/json',
        response_schema=list[question_schema],
    )

    try:
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config
        ):
            ans += chunk.text

        ans = ans.strip()
        if not ans.startswith('['):
            ans = '[' + ans
        if not ans.endswith(']'):
            ans = ans + ']'
            
        parsed_data = json.loads(ans)
        return json.dumps(parsed_data, ensure_ascii=False)
    except json.JSONDecodeError as e:
        print(f"Error in JSON response: {e}")
        print("Raw response:")
        print(ans[:200] + "..." if len(ans) > 200 else ans)
        return "[]"

if __name__ == "__main__":
    all_questions = []
    
    for i in range(0, 6):
        print(f"creating questions for intent_examples{i}.txt")
        try:
            response = create_questions(f"./intent_examples/intent_examples{i}.txt")
            questions_data = json.loads(response)
            
            for item in questions_data:
                if not isinstance(item, dict):
                    print(f"Invalid item structure in file {i}")
                    continue
                if "intent" not in item or "questions" not in item:
                    print(f"Missing required fields in item from file {i}")
                    continue
                if not isinstance(item["questions"], list) or len(item["questions"]) != 5:
                    print(f"Invalid questions format in item from file {i}")
                    continue
            
            with open(f'./intent_examples/example_questions{i}.json', 'w') as f:
                json.dump(questions_data, f, indent=2, ensure_ascii=False)
            all_questions.extend(questions_data)
        except Exception as e:
            print(f"Error processing file intent_examples{i}.txt: {e}")
            continue
    
    try:
        combined_json = json.dumps(all_questions, indent=2, ensure_ascii=False)
        with open('example_questions.json', 'w', encoding='utf-8') as f:
            f.write(combined_json)
        print(f"Successfully wrote {len(all_questions)} question sets to example_questions.json")
    except Exception as e:
        print(f"Error writing final JSON: {e}")