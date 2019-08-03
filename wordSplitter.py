#Incredibly important for finding all the matches inbetween observables and the string
import re
sub = ['P','Y','T','H','O','N','TH','PY','HO']

#This is my mapping function. It splits the word up in almost all the possible ways
#based on the observables you give it.
def wordSplitter(inp,subs,debug=False):
    l = []
    #Looks through the observables and finds if it matches somewhere in the word
    for i in subs:
        for match in re.finditer(r'(' + i + ')', inp):
            #Appends to a list the location where all the matches are.
            li = []
            for a in [match.span()]:
                li.append(list(a) + [i])
            
            l += li

    if debug:
        print(l)
        input('')
    
    #Gets all the starting points. Matches which were found at the start of the world.
    #e.g. FISSION. F is a match at the start.
    maps = []
    for i in l:
        if i[0] == 0:
            maps.append(i)

    if debug:
        print(maps)
        input('')

    #Recurses through the maps list and then ads on all the possible connecting pieces.
    #It continues until there is no pieces that connects to any of the maps anymore.
    #Here is the mapping process for FISSION. () for a finished state.
    #F
    #F.I
    #F.I.S, (F.I.SSION), F.I.SS
    #F.I.S.S, (F.I.S.SION), (F.I.SSION), F.I.SS.IO, F.I.SS.I
    #F.I.S.S.I, F.I.S.S.IO, (F.I.S.SION), (F.I.SSION), (F.I.SS.IO.N), F.I.SS.I.O
    #F.I.S.S.I.O, (F.I.S.S.IO.N), (F.I.S.SION), (F.I.SSION), (F.I.SS.IO.N), (F.I.SS.I.O.N)
    #(F.I.S.S.I.O.N), (F.I.S.S.IO.N), (F.I.S.SION), (F.I.SSION), (F.I.SS.IO.N), (F.I.SS.I.O.N)
    fin = False
    while not fin:
        nmaps = []
        fin = True
        for i in maps:
            if i[1] == len(inp):
                nmaps.append(i)

            else:
                for x in l:
                    if x[0] == i[1]:
                        nmaps.append([x[0], x[1], i[2] + '.' + x[2]])
                        fin = False
        
        maps = nmaps
    
        if debug:
            print(maps)
        

    for i in range(len(maps)):
        maps[i] = maps[i][2]

    maps = sorted(maps, key=len)
    reversed(maps)

    #Returns the mappings it got
    return maps

if __name__ == "__main__":
    wordSplitter('PYTHON',sub,True)