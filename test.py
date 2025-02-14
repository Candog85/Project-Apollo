import requests
import csv
import json




def requestinfo(schoolname='', schoolstate=''):

    count=0

    api="https://api.data.gov/ed/collegescorecard/v1/schools?api_key=fEZsVdtKgtVU4ODIpjHcP8vDttDK0ftSGZaWDcAk"

    queries={}
    request=''

    if schoolname:
        queries.update({"school.name":(f"{schoolname}")})
    
    if schoolstate:
        queries.update({"school.state":(f"{schoolstate}")})

    for query in queries:
        request+=(f"{query}={queries[query]}")
        count+=1
    
    request=f"{api}&{request}"

    test=requests.get(request).json()

    for key in test:{ 
        print(key,":", test[key]) 
    }
        
    return request

print(requestinfo("Harvard University"))
        


# print(test)
