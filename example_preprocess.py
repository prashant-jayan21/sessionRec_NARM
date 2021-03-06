import time
import csv
import pickle

import operator

import numpy as np

# Load .csv dataset
with open("data_raw/dataset-train-diginetica/train-item-views.csv", "rb") as f:
    reader = csv.DictReader(f, delimiter=';')
    sess_clicks = {}
    sess_date = {}
    ctr = 0
    curid = -1
    curdate = None
    for data in reader:
        sessid = data['sessionId']
        if curdate and not curid == sessid:
            date = time.mktime(time.strptime(curdate, '%Y-%m-%d'))
            sess_date[curid] = date
        curid = sessid
        item = data['itemId']
        curdate = data['eventdate']
        if sess_clicks.has_key(sessid):
            sess_clicks[sessid] += [item]
        else:
            sess_clicks[sessid] = [item]
        ctr += 1
        if ctr % 100000 == 0:
            print ('Loaded', ctr)
    date = time.mktime(time.strptime(curdate, '%Y-%m-%d'))
    sess_date[curid] = date

# Filter out length 1 sessions
for s in sess_clicks.keys():
    if len(sess_clicks[s]) == 1:
        del sess_clicks[s]
        del sess_date[s]

# Count number of times each item appears
iid_counts = {}
for s in sess_clicks:
    seq = sess_clicks[s]
    for iid in seq:
        if iid_counts.has_key(iid):
            iid_counts[iid] += 1
        else:
            iid_counts[iid] = 1

sorted_counts = sorted(iid_counts.items(), key=operator.itemgetter(1))

for s in sess_clicks.keys():
    curseq = sess_clicks[s]
    filseq = filter(lambda i: iid_counts[i] >= 5, curseq)
    if len(filseq) < 2:
        del sess_clicks[s]
        del sess_date[s]
    else:
        sess_clicks[s] = filseq

# Split out test set based on dates
dates = sess_date.items()
maxdate = dates[0][1]

for _, date in dates:
    if maxdate < date:
        maxdate = date

# 7 days for test
splitdate = maxdate - 86400 * 7
print('Split date', splitdate)
train_sess = filter(lambda x: x[1] < splitdate, dates)
test_sess = filter(lambda x: x[1] > splitdate, dates)

# Sort sessions by date
train_sess = sorted(train_sess, key=operator.itemgetter(1))
test_sess = sorted(test_sess, key=operator.itemgetter(1))

# Choosing item count >=5 gives approximately the same number of items as reported in paper
item_dict = {}
item_ctr = 1
train_seqs = []
train_dates = []
my_train_ctr = 0
# Convert training sessions to sequences and renumber items to start from 1
for s, date in train_sess:
    seq = sess_clicks[s]
    outseq = []
    for i in seq:
        if item_dict.has_key(i):
            outseq += [item_dict[i]]
        else:
            outseq += [item_ctr]
            item_dict[i] = item_ctr
            item_ctr += 1
    if len(outseq) < 2:  # Doesn't occur
        continue
    my_train_ctr += 1
    train_seqs += [outseq]
    train_dates += [date]

print("Number of training sessions:")
print(my_train_ctr)

test_seqs = []
test_dates = []
my_test_ctr = 0
# Convert test sessions to sequences, ignoring items that do not appear in training set
for s, date in test_sess:
    seq = sess_clicks[s]
    outseq = []
    for i in seq:
        if item_dict.has_key(i):
            outseq += [item_dict[i]]
    if len(outseq) < 2:
        continue
    my_test_ctr += 1
    test_seqs += [outseq]
    test_dates += [date]

print("Number of test sessions:")
print(my_test_ctr)

print("Number of items:")
print(len(item_dict))

# generate item feature matrix
with open("data_raw/dataset-train-diginetica/products.csv", "rb") as f:
    reader = csv.DictReader(f, delimiter=';')
    prices_dict = {} # mapped item id's to prices
    for data in reader:
        # {'itemId': '1', 'pricelog2': '10', 'product.name.tokens': '4875,776,56689,18212,18212,4896'}
        item_id = data['itemId']
        price = int(data['pricelog2'])

        if not item_dict.has_key(item_id):
            continue
        mapped_item_id = item_dict[item_id]

        prices_dict[mapped_item_id] = price

assert len(prices_dict) == len(item_dict)

with open("data_raw/dataset-train-diginetica/product-categories.csv", "rb") as f:
    reader = csv.DictReader(f, delimiter=';')
    categories_dict = {} # mapped item id's to category id's
    for data in reader:
        item_id = data['itemId']
        cat_id = int(data['categoryId'])

        if not item_dict.has_key(item_id):
            continue
        mapped_item_id = item_dict[item_id]

        categories_dict[mapped_item_id] = cat_id

assert len(categories_dict) == len(item_dict)

# map price to feature vector
all_unique_prices = list(set(prices_dict.values()))

def price_to_vec(price):
    vec = [0.0] * len(all_unique_prices)
    index = all_unique_prices.index(price)

    vec[index] = 1.0

    return vec

# map category to feature vector
all_unique_cats = list(set(categories_dict.values()))

def cat_to_vec(cat):
    vec = [0.0] * len(all_unique_cats)
    index = all_unique_cats.index(cat)

    vec[index] = 1.0

    return vec

# get all feature vectors
feature_matrix = np.random.rand(len(prices_dict), len(all_unique_prices) + len(all_unique_cats)) # items X feature vec size

for mapped_item_id, price in prices_dict.iteritems():
    cat = categories_dict[mapped_item_id]

    # mapped item id's start from 1, not 0
    row_index = mapped_item_id - 1
    price_feature_vec = price_to_vec(price)
    cat_feature_vec = cat_to_vec(cat)
    feature_vec = price_feature_vec + cat_feature_vec

    # insert
    feature_matrix[row_index] = feature_vec

def process_seqs(iseqs, idates):
    out_seqs = []
    out_dates = []
    labs = []
    for seq, date in zip(iseqs, idates):
        for i in range(1, len(seq)):
            tar = seq[-i]
            labs += [tar]
            out_seqs += [seq[:-i]]
            out_dates += [date]

    return out_seqs, out_dates, labs

tr_seqs, tr_dates, tr_labs = process_seqs(train_seqs,train_dates)
te_seqs, te_dates, te_labs = process_seqs(test_seqs,test_dates)

train = (tr_seqs, tr_labs)
test = (te_seqs, te_labs)

print("Number of training examples (sequences):")
print(len(tr_labs))
print("Number of test examples (sequences):")
print(len(te_labs))

f1 = open('data/digi_train.pkl', 'w')
pickle.dump(train, f1)
f1.close()
f2 = open('data/digi_test.pkl', 'w')
pickle.dump(test, f2)
f2.close()

np.save('data/digi_item_feature_matrix.npy', feature_matrix)

print('Done.')
