import random as rnd
def hraj_hru():
    historie=[]
    tajnecislo=rnd.randint(1,100 )
    tip=(-1)

    print("Myslím si číslo od 1 do 100.")

    while tip!=tajnecislo:
        tip=int(input("Tipni si číslo: "))

        if tip<tajnecislo:
            print("Myslím si větší číslo.")

        elif tip>tajnecislo:
            print("Myslím si menší číslo.")

        historie.append(tip)
    print("Uhádl jsi to!")
    print(f"Potřeboval jsi k tomu {len(historie)} pokusů.")
    print("Zde je tvá cesta k vítězství:")
    pocitadlo=1
    for tipcislo in historie:
        print(f"Tvůj {pocitadlo}. tip byl {tipcislo}")
        pocitadlo=pocitadlo+1
while True:
    hraj_hru()
    odpoved=input("Chceš hrát znovu? (ano/ne) ")
    if odpoved.lower=="ne":
        break