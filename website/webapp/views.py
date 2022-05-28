from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Case, When
from django.core.paginator import Paginator


from .models import Paper

#imports for pyserini and BERT
import os
import tensorflow
import json
import pandas as pd
import numpy as np
import string
import torch
import numpy
from tqdm import tqdm
from transformers import BertForQuestionAnswering
from transformers import BertTokenizer
from transformers import DistilBertTokenizer, DistilBertForQuestionAnswering

os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-1.11.0-openjdk-amd64"
os.environ["JVM_PATH"] = "/usr/lib/jvm/java-1.11.0-openjdk-amd64/lib/server/libjvm.so"
from pyserini.search import get_topics
#from pyserini.search import SimpleSearcher
from pyserini.search.lucene import LuceneSearcher



# Create your views here.

def BatchBertcall(question,abstractList):
    question_context_for_batch = []
    highlights_list=[]
    tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased', return_token_type_ids=True)
    model = DistilBertForQuestionAnswering.from_pretrained('distilbert-base-uncased-distilled-squad', return_dict=False)
    for context in abstractList:
        question_context_for_batch.append((question, context))

    model.config.max_position_embeddings =2048
    encoding = tokenizer.batch_encode_plus(question_context_for_batch,truncation= 'only_second', max_length =60, return_tensors="pt")
    input_ids, attention_mask = encoding["input_ids"], encoding["attention_mask"]
    start_scores, end_scores = model(input_ids, attention_mask=attention_mask)
    for index, (start_score, end_score, input_id) in enumerate(zip(start_scores, end_scores, input_ids)):
        max_startscore = torch.argmax(start_score)
        max_endscore = torch.argmax(end_score)
        ans_tokens = input_ids[index][max_startscore: max_endscore + 1]
        answer_tokens = tokenizer.convert_ids_to_tokens(ans_tokens, skip_special_tokens=True)
        answer_tokens_to_string = tokenizer.convert_tokens_to_string(answer_tokens)
        highlights_list.append(answer_tokens_to_string)
        #print ("\nQuestion: ",question)
        #print ("Answer: ", answer_tokens_to_string)
    return highlights_list




def search(request):
    query = request.GET.get('q', '')
    page_number = request.GET.get('p', '1')
    paper_ids=[]
    searcher = LuceneSearcher('/users/stud/a/awadin00/testpyserini/indexes/')
#    tokenizer = BertTokenizer.from_pretrained('bert-large-uncased-whole-word-masking-finetuned-squad')
 #   model = BertForQuestionAnswering.from_pretrained('bert-large-uncased-whole-word-masking-finetuned-squad')


    #searcher=SimpleSearcher('/users/stud/a/awadin00/testpyserini/indexes/')

    if query:
        # Retreive papers from pyserini
        hits = searcher.search(query)
        limitanswer=20
        lenhits= len(hits)
        if lenhits==0:
            return render(request, 'webapp/index_noresult.html')


        elif lenhits<limitanswer:
            limitanswer=lenhits

        for i in range(0, limitanswer):
            paper_ids.append(hits[i].docid)
#        paper_ids = [7, 8]
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(paper_ids)])
        queryset = Paper.objects.filter(pk__in=paper_ids).order_by(preserved)
        abstracts = [paper.abstract for paper in queryset.all()]
        highlights = BatchBertcall(query, abstracts)
        paginator = Paginator(list(zip(queryset, highlights)), 10) # Show 3 per page.
        page = paginator.get_page(page_number)

        context = {'page': page, 'query': query}
        return render(request, 'webapp/search.html', context)
    
    return render(request, 'webapp/index.html')

def about(request):
    return render(request, 'webapp/about.html')
