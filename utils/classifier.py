import json
from openai import OpenAI
from storage.sql_db import Database
from utils.util import is_valid_list
import os

OPEN_AI_API_KEY = os.getenv("OPEN_AI_KEY")


class Classify:
    sdgs = [
        {"themeID": "SDG1"},
        {"themeID": "SDG2"},
        {"themeID": "SDG3"},
        {"themeID": "SDG4"},
        {"themeID": "SDG5"},
        {"themeID": "SDG6"},
        {"themeID": "SDG7"},
        {"themeID": "SDG8"},
        {"themeID": "SDG9"},
        {"themeID": "SDG10"},
        {"themeID": "SDG11"},
        {"themeID": "SDG12"},
        {"themeID": "SDG13"},
        {"themeID": "SDG14"},
        {"themeID": "SDG15"},
        {"themeID": "SDG16"},
        {"themeID": "SDG17"},
    ]

    def class_by_sdgs(self, db: Database):
        try:
            API_KEY = OPEN_AI_API_KEY

            # oapi.api_key = API_KEY
            client = OpenAI(
                api_key=API_KEY
            )

            # js = open('./hdx.new.json')
            # datasets_list = json.load(js)

            datasets = db.get_all_links_by_publishment_status(0, 1000)

            index = 0
            counter = 0
            loop = 0
            for dataset in datasets:

                # dataset = datasets[index+i]

                if counter == 60:
                    # print("No OPEN AI USED HERE")
                    pass

                else:
                    print(f"{counter}. {dataset.name}:")
                    print(f"{dataset.data}: \n")
                    # Call OPEN AI
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Please learn about the 17 SDG Goals by the UN, their tagest and indicators to respond to the following questions"},
                            {"role": "user", "content": "Based on the 17 SDGS by the United nation and based on the following datasets description, can you clssify the dataset to the Goal it mostly corresponds to? Please do not give more than 2 classifications"},
                            {"role": "user",
                                "content": "The following is the dataset description"},
                            {"role": "user", "content": f"{dataset.name}, {dataset.description}, {dataset.tags}"},
                            {"role": "system",
                                "content": "Give your answers in a python list."},
                            {"role": "system",
                                "content": "If not sure, return an empty list like []"},
                            {"role": "system",
                                "content": "Example of acceptable answers : [1,3], [2,12], [1], [10] Examples of unacceptable answers ['Economy'], ['1'], ['Goal 1'], ['1: Hanger']"},

                        ]
                    )
                    ans = response.choices[0].message.content
                    print(ans)
                    goals_list = []
                    try:
                        goals_list = json.loads(ans)
                    except Exception as e:
                        pass
                    if is_valid_list(goals_list) or len(goals_list) == 0:
                        themes = []
                        for i in goals_list:
                            print("OK")

                            themes.append(self.sdgs[i-1])
                            # print(type(ans))
                        # CLASSIFY
                        db.update_thems(str(themes), dataset.hash_value)

                    counter = counter + 1

                # index = i * 100
                loop = loop + 1
                if loop % 100 == 0:
                    counter = 0
                    index = index + 1

            print(f"Sections {index}")
        except Exception as e:
            print(e)
