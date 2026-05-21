import re
import random
import streamlit as st
import plotly.graph_objects as go
from collections import defaultdict

# PREPROCESSING
def preprocess(text: str, order: int = 1) -> list[str]:
    text = text.lower()
    text = re.sub(r"(?<=[a-z])'(?=[a-z])", "apostrophe", text)
    text = re.sub(r"[^a-z ]", " ", text)
    text = text.replace("apostrophe", "'")
    text = re.sub(r" +", " ", text).strip()
    tokens = text.split()
    if len(tokens) <= order:
        raise ValueError(f"Corpus too short: {len(tokens)} tokens.")
    return tokens

# COUNT MATRIX

def build_count_matrix(tokens: list[str], order: int = 1) -> dict:
    counts = defaultdict(lambda: defaultdict(int))
    for i in range(len(tokens) - order):
        state     = tuple(tokens[i : i + order])
        next_word = tokens[i + order]
        counts[state][next_word] += 1
    return counts

#PROBABILITY MATRIX

def build_probability_matrix(counts: dict) -> dict:
    probs = {}

    for state, next_words in counts.items():
        total = sum(next_words.values())
        probs[state] = {w: c / total for w, c in next_words.items()}
    return probs

# PREDICT NEXT WORD

def predict_next(probs: dict, input_text: str, order: int = 1, top_n: int = 3) -> list[tuple]:
    tokens = input_text.lower().split()
    if len(tokens) < order:
        return []
    state =tuple(tokens[-order:])
    if state not in probs:
        return []
    ranked=sorted(probs[state].items(), key=lambda x: x[1], reverse=True)
    return ranked[:top_n]

#INCREMENTAL UPDATE

def incremental_update(counts, probs, tokens, new_word, order=1):
    if len(tokens) < order:
        tokens.append(new_word)
        return counts, probs, tokens
    affected_state = tuple(tokens[-order:])
    counts[affected_state][new_word] += 1
    total = sum(counts[affected_state].values())
    probs[affected_state] = {w: c / total for w, c in counts[affected_state].items()}
    tokens.append(new_word)
    return counts, probs, tokens

#VISUALIZATION

def plot_transition_heatmap(probs: dict, top_n: int = 10):
    states = sorted(probs.keys(), key=lambda s: sum(probs[s].values()), reverse=True)[:top_n]
    all_words = sorted({w for s in states for w in probs[s]})

    state_labels = [" ".join(s) for s in states]
    matrix = [
        [probs[s].get(w, 0.0) for w in all_words]
        for s in states
    ]

    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=all_words,
        y=state_labels,
        colorscale="Blues",
        text=[[f"{v:.2f}" if v > 0 else "" for v in row] for row in matrix],
        texttemplate="%{text}",
        hovertemplate="from: %{y}<br>to: %{x}<br>P = %{z:.3f}<extra></extra>",
    ))
    fig.update_layout(
        title="Transition probability heatmap",
        xaxis_title="Next word",
        yaxis_title="Current state",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig

# STREAMLIT UI ──────────────────────────────────────────────────────────────

st.set_page_config(page_title="Markov Next-Word Predictor", page_icon="🔤", layout="wide")
st.title("🔤 Markov Chain — Next Word Predictor")

# Sidebar controls
with st.sidebar:
    st.header("Settings")
    order = st.slider("Markov order", min_value=1, max_value=3, value=1,
                      help="1 = last word predicts next. 2 = last 2 words predict next.")
    top_n = st.slider("Suggestions to show", min_value=1, max_value=8, value=3)
    st.divider()
    st.header("Corpus")
    corpus_choice = st.radio("Use:", ["Built-in sample", "Paste your own"])

    default_corpus = (
        '''
        hello bilbo baggins
2 THE LORD OF THE RINGS 


They seldom now reach three feet; but they have dwindled, they say, 
and in ancient days they were taller. According to the Red Book, 
Bandobras Took (Bullroarer), son of Isumbras the Third, was four 
foot five and able to ride a horse. He was surpassed in all Hobbit 
records only by two famous characters of old; but that curious matter 
is dealt with in this book. 

As for the Hobbits of the Shire, with whom these tales are con- 
cerned, in the days of their peace and prosperity they were a merry 
folk. They dressed in bright colours, being notably fond of yellow 
and green; but they seldom wore shoes, since their feet had tough 
leathery soles and were clad in a thick curling hair, much like the 
hair of their heads, which was commonly brown. Thus, the only craft 
little practised among them was shoe-making; but they had long and 
skilful fingers and could make many other useful and comely things. 
Their faces were as a rule good-natured rather than beautiful, broad, 
bright-eyed, red-cheeked, with mouths apt to laughter, and to eating 
and drinking. And laugh they did, and eat, and drink, often and 
heartily, being fond of simple jests at all times, and of six meals a 
day (when they could get them). They were hospitable and delighted 
in parties, and in presents, which they gave away freely and eagerly 
accepted. 

It is plain indeed that in spite of later estrangement Hobbits are 
relatives of ours: far nearer to us than Elves, or even than Dwarves. 
Of old they spoke the languages of Men, after their own fashion, and 
liked and disliked much the same things as Men did. But what exactly 
our relationship is can no longer be discovered. The beginning of 
Hobbits lies far back in the Elder Days that are now lost and forgotten. 
Only the Elves still preserve any records of that vanished time, and 
their traditions are concerned almost entirely with their own history, 
in which Men appear seldom and Hobbits are not mentioned at all. 
Yet it is clear that Hobbits had, in fact, lived quietly in Middle-earth 
for many long years before other folk became even aware of them. 
And the world being after all full of strange creatures beyond count, 
these little people seemed of very little importance. But in the days 
of Bilbo, and of Frodo his heir, they suddenly became, by no wish 
of their own, both important and renowned, and troubled the 
counsels of the Wise and the Great. 


Those days, the Third Age of Middle-earth, are now long past, 
and the shape of all lands has been changed; but the regions in which 
Hobbits then lived were doubtless the same as those in which they 
still linger: the North-West of the Old World, east of the Sea. Of their 
original home the Hobbits in Bilbo’s time preserved no knowledge. A 
love of learning (other than genealogical lore) was far from general 


PROLOGUE 3 


among them, but there remained still a few in the older families who 
studied their own books, and even gathered reports of old times and 
distant lands from Elves, Dwarves, and Men. Their own records 
began only after the settlement of the Shire, and their most ancient 
legends hardly looked further back than their Wandering Days. It is 
clear, nonetheless, from these legends, and from the evidence of their 
peculiar words and customs, that like many other folk Hobbits had 
in the distant past moved westward. Their earliest tales seem to 
glimpse a time when they dwelt in the upper vales of Anduin, between 
the eaves of Greenwood the Great and the Misty Mountains. Why 
they later undertook the hard and perilous crossing of the mountains 
into Eriador is no longer certain. Their own accounts speak of the 
multiplying of Men in the land, and of a shadow that fell on the 
forest, so that it became darkened and its new name was Mirkwood. 

Before the crossing of the mountains the Hobbits had already 
become divided into three somewhat different breeds: Harfoots, 
Stoors, and Fallohides. The Harfoots were browner of skin, smaller, 
and shorter, and they were beardless and bootless; their hands and 
feet were neat and nimble; and they preferred highlands and hillsides. 
The Stoors were broader, heavier in build; their feet and hands were 
larger; and they preferred flat lands and riversides. The Fallohides 
were fairer of skin and also of hair, and they were taller and slimmer 
than the others; they were lovers of trees and of woodlands. 

The Harfoots had much to do with Dwarves in ancient times, and 
long lived in the foothills of the mountains. They moved westward 
early, and roamed over Eriador as far as Weathertop while the others 
were still in Wilderland. They were the most normal and repre- 
sentative variety of Hobbit, and far the most numerous. They were 
the most inclined to settle in one place, and longest preserved their 
ancestral habit of living in tunnels and holes. 

The Stoors lingered long by the banks of the Great River Anduin, 
and were less shy of Men. They came west after the Harfoots and 
followed the course of the Loudwater southwards; and there many 
of them long dwelt between Tharbad and the borders of Dunland 
before they moved north again. 

The Fallohides, the least numerous, were a northerly branch. They 
were more friendly with Elves than the other Hobbits were, and had 
more skill in language and song than in handicrafts; and of old they 
preferred hunting to tilling. They crossed the mountains north of 
Rivendell and came down the River Hoarwell. In Eriador they soon 
mingled with the other kinds that had preceded them, but being 
somewhat bolder and more adventurous, they were often found as 
leaders or chieftains among clans of Harfoots or Stoors. Even in 
Bilbo’s time the strong Fallohidish strain could still be noted among 


4 THE LORD OF THE RINGS 


the greater families, such as the Tooks and the Masters of Buckland. 

In the westlands of Eriador, between the Misty Mountains and 
the Mountains of Lune, the Hobbits found both Men and Elves. 
Indeed, a remnant still dwelt there of the Dunedain, the kings of 
Men that came over the Sea out of Westernesse; but they were dwin- 
dling fast and the lands of their North Kingdom were falling far and 
wide into waste. There was room and to spare for incomers, and ere 
long the Hobbits began to settle in ordered communities. Most of 
their earlier settlements had long disappeared and been forgotten in 
Bilbo’s time; but one of the first to become important still endured, 
though reduced in size; this was at Bree and in the Chetwood that 
lay round about, some forty miles east of the Shire. 

It was in these early days, doubtless, that the Hobbits learned their 
letters and began to write after the manner of the Duinedain, who 
had in their turn long before learned the art from the Elves. And in 
those days also they forgot whatever languages they had used before, 
and spoke ever after the Common Speech, the Westron as it was 
named, that was current through all the lands of the kings from Arnor 
to Gondor, and about all the coasts of the Sea from Belfalas to Lune. 
Yet they kept a few words of their own, as well as their own names 
of months and days, and a great store of personal names out of 
the past. 

About this time legend among the Hobbits first becomes history 
with a reckoning of years. For it was in the one thousand six hundred 
and first year of the Third Age that the Fallohide brothers, Marcho 
and Blanco, set out from Bree; and having obtained permission from 
the high king at Fornost,* they crossed the brown river Baranduin 
with a great following of Hobbits. They passed over the Bridge of 
Stonebows, that had been built in the days of the power of the North 
Kingdom, and they took all the land beyond to dwell in, between 
the river and the Far Downs. All that was demanded of them was 
that they should keep the Great Bridge in repair, and all other bridges 
and roads, speed the king’s messengers, and acknowledge his 
lordship. 

Thus began the Shire-reckoning, for the year of the crossing of the 
Brandywine (as the Hobbits turned the name) became Year One of 
the Shire, and all later dates were reckoned from it.t At once the 
western Hobbits fell in love with their new land, and they remained 
there, and soon passed once more out of the history of Men and of 
Elves. While there was still a king they were in name his subjects, 


* As the records of Gondor relate this was Argeleb II, the twentieth of the Northern 
line, which came to an end with Arvedui three hundred years later. 

+ Thus, the years of the Third Age in the reckoning of the Elves and the Dunedain 
may be found by adding 1600 to the dates of Shire-reckoning. 


PROLOGUE 5 


but they were, in fact, ruled by their own chieftains and meddled not 
at all with events in the world outside. To the last battle at Fornost 
with the Witch-lord of Angmar they sent some bowmen to the aid 
of the king, or so they maintained, though no tales of Men record 
it. But in that war the North Kingdom ended; and then the Hobbits 
took the land for their own, and they chose from their own chiefs a 
Thain to hold the authority of the king that was gone. There for a 
thousand years they were little troubled by wars, and they prospered 
and multiplied after the Dark Plague (S.R. 37) until the disaster of 
the Long Winter and the famine that followed it. Many thousands 
then perished, but the Days of Dearth (1158-60) were at the time of 
this tale long past and the Hobbits had again become accustomed 
to plenty. The land was rich and kindly, and though it had long been 
deserted when they entered it, it had before been well tilled, and 
there the king had once had many farms, cornlands, vineyards, and 
woods. 

Forty leagues it stretched from the Far Downs to the Brandywine 
Bridge, and fifty from the northern moors to the marshes in the south. 
The Hobbits named it the Shire, as the region of the authority of 
their Thain, and a district of well-ordered business; and there in that 
pleasant corner of the world they plied their well-ordered business 
of living, and they heeded less and less the world outside where dark 
things moved, until they came to think that peace and plenty were 
the rule in Middle-earth and the right of all sensible folk. They forgot 
or ignored what little they had ever known of the Guardians, and of 
the labours of those that made possible the long peace of the Shire. 
They were, in fact, sheltered, but they had ceased to remember it. 

At no time had Hobbits of any kind been warlike, and they had 
never fought among themselves. In olden days they had, of course, 
been often obliged to fight to maintain themselves in a hard world; 
but in Bilbo’s time that was very ancient history. The last battle, 
before this story opens, and indeed the only one that had ever been 
fought within the borders of the Shire, was beyond living memory: 
the Battle of Greenfields, S.R. 1147, in which Bandobras Took routed 
an invasion of Orcs. Even the weathers had grown milder, and the 
wolves that had once come ravening out of the North in bitter white 
winters were now only a grandfather’s tale. So, though there was 
still some store of weapons in the Shire, these were used mostly as 
trophies, hanging above hearths or on walls, or gathered into the 
museum at Michel Delving. The Mathom-house it was called; for 
anything that Hobbits had no immediate use for, but were unwilling 
to throw away, they called a mathom. Their dwellings were apt to 
become rather crowded with mathoms, and many of the presents 
that passed from hand to hand were of that sort. 


6 THE LORD OF THE RINGS 


Nonetheless, ease and peace had left this people still curiously 
tough. They were, if it came to it, difficult to daunt or to kill; and 
they were, perhaps, so unwearyingly fond of good things not least 
because they could, when put to it, do without them, and could 
survive rough handling by grief, foe, or weather in a way that aston- 
ished those who did not know them well and looked no further than 
their bellies and their well-fed faces. Though slow to quarrel, and for 
sport killing nothing that lived, they were doughty at bay, and at 
need could still handle arms. They shot well with the bow, for they 
were keen-eyed and sure at the mark. Not only with bows and arrows. 
If any Hobbit stooped for a stone, it was well to get quickly under 
cover, as all trespassing beasts knew very well. 

All Hobbits had originally lived in holes in the ground, or so they 
believed, and in such dwellings they still felt most at home; but in 
the course of time they had been obliged to adopt other forms of 
abode. Actually in the Shire in Bilbo’s days it was, as a rule, only 
the richest and the poorest Hobbits that maintained the old custom. 
The poorest went on living in burrows of the most primitive kind, 
mere holes indeed, with only one window or none; while the well- 
to-do still constructed more luxurious versions of the simple diggings 
of old. But suitable sites for these large and ramifying tunnels (or 
smials as they called them) were not everywhere to be found; and in 
the flats and the low-lying districts the Hobbits, as they multiplied, 
began to build above ground. Indeed, even in the hilly regions and 
the older villages, such as Hobbiton or Tuckborough, or in the chief 
township of the Shire, Michel Delving on the White Downs, there 
were now many houses of wood, brick, or stone. These were specially 
favoured by millers, smiths, ropers, and cartwrights, and others of 
that sort; for even when they had holes to live in, Hobbits had long 
been accustomed to build sheds and workshops. 

The habit of building farmhouses and barns was said to have begun 
among the inhabitants of the Marish down by the Brandywine. The 
Hobbits of that quarter, the Eastfarthing, were rather large and heavy- 
legged, and they wore dwarf-boots in muddy weather. But they were 
well known to be Stoors in a large part of their blood, as indeed was 
shown by the down that many grew on their chins. No Harfoot or 
Fallohide had any trace of a beard. Indeed, the folk of the Marish, 
and of Buckland, east of the River, which they afterwards occupied, 
came for the most part later into the Shire up from south-away; and 
they still had many peculiar names and strange words not found 
elsewhere in the Shire. 

It is probable that the craft of building, as many other crafts beside, 
was derived from the Dunedain. But the Hobbits may have learned 
it direct from the Elves, the teachers of Men in their youth.
        '''
    )

    if corpus_choice == "Paste your own":
        raw_corpus = st.text_area("Your corpus", height=200,
                                  placeholder="Paste a large block of text here...")
    else:
        raw_corpus = default_corpus
        st.caption("Using built-in sample corpus.")

# ── Build model (cached by corpus + order) ──
@st.cache_resource
def build_model(raw: str, ord_: int):
    tokens = preprocess(raw, order=ord_)
    counts = build_count_matrix(tokens, order=ord_)
    probs  = build_probability_matrix(counts)
    return tokens, counts, probs

if not raw_corpus.strip():
    st.info("Paste a corpus in the sidebar to get started.")
    st.stop()

try:
    tokens, counts, probs = build_model(raw_corpus, order)
except ValueError as e:
    st.error(str(e))
    st.stop()

st.success(f"Model ready — {len(tokens)} tokens, {len(probs)} unique states.")

# ── Main: next word predictor ──
st.subheader("Type your text")
user_input = st.text_input(
    label="Input",
    placeholder="Start typing...",
    label_visibility="collapsed"
)

if user_input.strip():
    predictions = predict_next(probs, user_input, order=order, top_n=top_n)

    if predictions:
        st.markdown("**Suggestions:**")
        cols = st.columns(len(predictions))
        for col, (word, prob) in zip(cols, predictions):
            col.metric(label=f"{prob*100:.1f}%", value=word)
    else:
        st.warning(
            f"No predictions — the last {order} word(s) of your input "
            f"were never seen in the corpus."
        )

# ── Incremental update section ──
st.divider()
st.subheader("Add a new word to the corpus")
st.caption("Teaches the model a new transition without retraining from scratch.")

col1, col2 = st.columns([3, 1])
with col1:
    new_word = st.text_input("New word to add", placeholder="e.g. jumped",
                              label_visibility="collapsed")
with col2:
    add_btn = st.button("Add word", use_container_width=True)

if add_btn and new_word.strip():
    cleaned = new_word.strip().lower()
    counts, probs, tokens = incremental_update(counts, probs, tokens, cleaned, order=order)
    st.success(f"Added '{cleaned}' — corpus now {len(tokens)} tokens.")

#Heatmap
st.divider()
st.subheader("Transition probability heatmap")
st.caption("Rows = current state. Columns = possible next words. Color = probability.")
st.plotly_chart(plot_transition_heatmap(probs, top_n=10), use_container_width=True)

#Raw model inspector
with st.expander("Inspect the probability matrix"):
    query = st.text_input("Look up a state", placeholder="e.g. the cat")
    if query.strip():
        state_key = tuple(query.strip().lower().split()[-order:])
        if state_key in probs:
            st.write(f"Transitions from `{' '.join(state_key)}`:")
            ranked = sorted(probs[state_key].items(), key=lambda x: x[1], reverse=True)
            for word, prob in ranked:
                st.progress(prob, text=f"{word}  —  {prob*100:.1f}%")
        else:
            st.warning("State not found in model.")