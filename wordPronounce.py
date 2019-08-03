#This remembers the object that has been taught. Very important because otherwise it would have to relearn.
import pickle
#This is a function which maps words
from wordSplitter import wordSplitter
#Helps with word manipulations. In this context, for easy string subbing.
import re
#Important for putting the Wavs together.
from pydub import AudioSegment
#Needed to play the created mashed together sounds
from playsound import playsound
#Important for file manipulation.
import os
#Tempfile is really only here to create a random filename
import tempfile

#file to take wavs from
wavFile = 'Balanced_Wavs'

#This is to dispose of all the wavs from the last session
for i in os.listdir(f'{wavFile}'):
    if i.startswith("1"):
        os.remove(os.path.join(f'{wavFile}', i))

exceptions = {
    'I':'AY',
    'YOU':'Y UW',
    'WE':'W IY',
    'WHAT':'W AH T'
}

class Pronounce:
    def __init__(self):
        #Hidden Markov Model Variables

        #The phonemes. Aka the hidden states.
        self.states = ()

        #Emission probabilities of the hidden states.
        #How likely it is to output an observable state.
        self.emit_p = {}

        #Transition probabilities between the hidden states.
        #How likely it is to transition to another phoneme at next state.
        self.trans_p = {}

        #The likelihood of starting with a certain phoneme.
        self.initial = [{}, 0]

        #This is for debugging, but it tells all the observable states.
        self.emits = ()

    def pronounce(self, inp, debug=False):
        #Gets the input and puts it in uppercase format, which my HMM learned in.
        inp = inp.upper()
        #Splits the sentence
        sent = inp
        sent = re.split('\.|,', sent)

        for i in range(len(sent)):
            sent[i] = sent[i].strip()
            sent[i] = sent[i].split(' ')

        #Puts each word in sentence through my word mapper to get almost all the mappings of the word
        #and puts the word through the viterbi algorithm to find the mapping which has the most confidence.
        #It then appends the most probable mapping's pronounciation to sentPro.
        sentPro = self.mostLikely(sent, debug)
        if debug:
            input('')

        #This gets rid of the probability section of the words in sentPro
        for x in range(len(sentPro)):
            for i in range(len(sentPro[x])):
                try:
                    #This part removes any numbers or spaces of dashes in the pronounciations.
                    #The numbers are lexical stress. But I struggled saying even the base sounds.
                    #So everything now has the same amount of stress put on it.
                    sentPro[x][i] = re.split('\s\s|-', ' '.join(sentPro[x][i]))
                    for a in range(len(sentPro[x][i])):
                        sentPro[x][i][a] = re.sub(r'\s|[0-9]','',sentPro[x][i][a])
                
                except:
                    print(sentPro[x][i])

        #This goes through the pronounciations and then appends their mp3 sounds to this sounds list.
        #This uses pydub. It also annoyingly is what makes saying a sentence take a long time for my bot.
        #The rest is basically instantaneous.
        sounds = []
        for x in range(len(sentPro)):
            for i in sentPro[x]:
                for a in i:
                    sounds.append(AudioSegment.from_wav(f'{wavFile}/{a}.wav'))
                #Appends 100 ms of silence after every word pronounciations
                silence = AudioSegment.from_mp3(f'{wavFile}/Silence.wav')
                sounds.append(silence[:300])

            silence = AudioSegment.from_mp3(f'{wavFile}/Silence.wav')
            sounds.append(silence[:500])

        #Adds all the sounds together
        sentence = sounds[0]
        for i in sounds[1:]:
            sentence += i

        #I had permission issues but found out that I had no issues when
        #I tampered with a file once. So I have to create a new file with a unique
        #name. For every single session of use for my model.
        #The tempfile function creates a random name.
        #I use playsound to play the file. Export creates the wav.
        fName = next(tempfile._get_candidate_names())
        sentence.export(f'{wavFile}/1{fName}.wav', format='wav')
        playsound(f'{wavFile}/1{fName}.wav')
        
        #I also return the sentence phonemes. Mainly because it's hard to understand my voice.
        #I wasn't able to record pure sounds properly.
        return sentPro

    def mostLikely(self, sent, debug=True):
        #Puts each word in sentence through my word mapper to get almost all the mappings of the word
        #and puts the word through the viterbi algorithm to find the mapping which has the most confidence.
        #It then appends the most probable mapping's pronounciation to sentPro.
        sentPro = []
        stepSize = 10
        for a in range(len(sent)):
            sentP = []
            for x in sent[a]:
                if x in exceptions:
                    result = (exceptions[x], 0)
                else:
                    #wordSplitter is my function that find all the mappings
                    maps = [i for i in wordSplitter(x, self.emits)]
                    if debug:
                        print(f'{len(maps)} maps')
                    result = (0,0)
                    #Looks through all the viterbi outputs for all the mappings
                    for i in range(0, len(maps), stepSize):
                        if i+stepSize > len(maps):
                            g = len(maps)
                        else:
                            g = i + stepSize

                        if debug:
                            #print(i)
                            print(maps[i:g])

                        for a in maps[i:g]:
                            #Replaces current result if algorithm says that current pronounciation is more likely
                            posResult = self.viterbi(a.split('.'))
                            if posResult[1] > result[1]:
                                result = posResult
                        
                        #Puts result in sentPro
                        if result[1] != 0:
                            if debug:
                                print(result[0])
                            break

                sentP.append(result[0])
            sentPro.append(sentP)

        return sentPro

    def viterbi(self, obs):
        V = [{}]

        if len(obs) == 0:
            return []

        #Sets up the initial probabilities based on the first observed state
        for st in self.states:
            #Finds the overall initial probability by multiplying the probability of event given state by the probability of the state initially
            V[0][st] = {"prob": self.initial[0][st] * self.emit_p[st][0][obs[0]], "prev": None}

        # Run when length of observed is greater than 1
        for t in range(1, len(obs)):

            #Create a new set of probabilities for the next observation
            V.append({})

            for st in self.states:
                #Find the starting maximum probability from the probability of a starting tag given previous tag probability and transition probability
                max_tr_prob = V[t-1][self.states[0]]["prob"]*self.trans_p[self.states[0]][0][st]

                #Stores the selected most probable state 
                prev_st_selected = self.states[0]

                for prev_st in self.states[1:]:
                    #Gets the probability of a state given a previous state chance of transition and its probability
                    tr_prob = V[t-1][prev_st]["prob"]*self.trans_p[prev_st][0][st]

                    #If the found probability is greater than the max probability, change it to the new one
                    if tr_prob > max_tr_prob:

                        max_tr_prob = tr_prob

                        #Also change the probable previous state to the one transitioned from by the new probability
                        prev_st_selected = prev_st

                        
                #Get overall max probability of tag from maximum transition probability and the probability that it emitted the observed state
                max_prob = max_tr_prob * self.emit_p[st][0][obs[t]]
                
                #Set the overall probability of the tag and the state it came from
                V[t][st] = {"prob": max_prob, "prev": prev_st_selected}

        opt = []

        # Get the highest possible probable value for the final observed state
        max_prob = max(value["prob"] for value in V[-1].values())

        previous = None

        #Find that most probable final state
        for st, data in V[-1].items():
            if data["prob"] == max_prob:

                opt.append(st)

                previous = st

                break

        # Backtrack down and append
        for t in range(len(V) - 2, -1, -1):

            opt.append(V[t + 1][previous]["prev"])

            previous = V[t + 1][previous]["prev"]

        opt = ' '.join(reversed(opt))

        #returns pronounciation, and its probability.
        return (opt, max_prob)

    def learn(self, file):
        #Looks through file it needs to learn
        with open(file, 'r') as f:
            #splits file into lines
            inp = f.readlines()
            #Looks through lines
            for i in inp:
                #Gets rid of the \n and splits by space
                a = i.strip().split(' ')
                #the phonemes are everything excluding the first slot
                phonemes = a[1:]
                #splits the first slot in to its multiple parts
                word = a[0].strip().split('.')
                #removes blank space from word parts. It sometimes appears and I can't track it down.
                if '' in word:
                    word.remove('')

                #Checks if all phonemes can pair up with a piece of the word
                if len(phonemes) == len(word):
                    #Updates the emission probabilities of the phonemes based on the word piece it is paired with
                    for i in range(len(phonemes)):
                        self.emit_p[phonemes[i]][1] += 1
                        self.emit_p[phonemes[i]][0][word[i]] += 1

                        #Also updates the transition probabilities between the phonemes,
                        #based on the phoneme previous to the current phoneme it is looking at.
                        #Doesn't try to update if no phoneme is before the current one.
                        if i > 0:
                            self.trans_p[phonemes[i-1]][1] += 1
                            self.trans_p[phonemes[i-1]][0][phonemes[i]] += 1

                    #Updates the initial phoneme probabilities based on the first phoneme of the word.
                    self.initial[0][phonemes[0]] += 1
                    self.initial[1] += 1

        #Changes the emission probabilities into the fraction form
        for i in self.emit_p:
            for x in self.emit_p[i][0]:
                if self.emit_p[i][0][x] > 0:
                    self.emit_p[i][0][x] = self.emit_p[i][0][x]/self.emit_p[i][1]

        #Changes the transition probabilities into the fraction form
        for i in self.trans_p:
            for x in self.trans_p[i][0]:
                if self.trans_p[i][0][x] > 0:
                    self.trans_p[i][0][x] = self.trans_p[i][0][x]/self.trans_p[i][1]

        #Changes the initial probabilities into the fraction form
        for i in self.initial[0]:
            self.initial[0][i] = self.initial[0][i]/self.initial[1]
            

    def addStates(self, file):
        #Gets the states and emits and makes them into sets
        self.states = set(self.states)
        self.emits = set(self.emits)

        #reads through the learning file
        with open(file, 'r') as f:
            #Reads through each line
            lines = f.readlines()
            for i in lines:
                wordSplit = i.strip().split(' ')
                #Adds all the phonemes it sees to the states set
                for i in wordSplit[1:]:
                    self.states.add(i)
                
                wordSplit = wordSplit[0].split('.')
                for i in wordSplit:
                    #Adds all the observables it sees to the emits set
                    self.emits.add(i)

        #Removes the random black observable. Again I can't find what is causing it in the dataset.
        self.emits.remove('')

        #Makes the states and emits into tuples. Mainly because I want the immutable.
        self.states = tuple(self.states)
        self.emits = tuple(self.emits)

        #Sets up the connections for the probabilities
        
        #Sets up the connections between all the states and all the emits
        #at a probability of 0
        for x in self.states:
            self.emit_p[x] = [{}, 0]
            for i in self.emits:
                self.emit_p[x][0][i] = 0    

        #Sets up the connections between all the states and the rest of the states including themselves 
        #at a probability of 0
        for x in self.states:
            self.trans_p[x] = [{}, 0]
            for i in self.states:
                self.trans_p[x][0][i] = 0

        #Sets up all initial probabilities for phonemes to 0
        for x in self.states:
            self.initial[0][x] = 0

#Some functions for ease of telling my HMM to learn, and also saving it once it does learn.
#It learns from useableWords.txt.
def createObj():
    hmm = Pronounce()
    hmm.addStates('useableWords.txt')
    hmm.learn('useableWords.txt')
    pickle.dump(hmm, open("sav.p", "wb"))
    return hmm

def getObj():
    hmm = pickle.load(open("sav.p", "rb"))
    return hmm

hmm = createObj()