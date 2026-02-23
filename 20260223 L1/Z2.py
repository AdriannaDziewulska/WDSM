import math
import matplotlib.pyplot as plt
import time


class Generator:
    def __init__(self,ziarno=1):
        self.a=16807
        self.b=0
        self.c=2147483647
        self.x=ziarno
    def gen_u01(self):
        self.x=(self.a*self.x+self.b)%self.c
        return self.x/self.c


def gen_poisson(rng,lam,n):
    wyniki=[]
    q=math.exp(-lam)
    for _ in range(n):
        X=-1
        s=1.0
        while s>q:
            s*=rng.gen_u01()
            X+=1
        wyniki.append(X)
    return wyniki


def gen_normalny(rng,mu,sigma,n):
    wyniki=[]
    for _ in range(math.ceil(n/2)):
        u1=rng.gen_u01()
        u2=rng.gen_u01()
        r=math.sqrt(-2*math.log(u1))
        th=2*math.pi*u2
        wyniki.append(mu+sigma*(r*math.cos(th)))
        wyniki.append(mu+sigma*(r*math.sin(th)))
    return wyniki[:n]


z_in=input("Ziarno? (t/n): ").lower()
seed=int(input("Podaj ziarno: ")) if z_in=='t' else int(time.time()*1000)%2147483647
rng=Generator(seed)
n=int(input("N: "))
la=float(input("Lambda: "))
d_p=gen_poisson(rng,la,n)
mu=float(input("Mu: "))
si=float(input("Sigma: "))
d_n=gen_normalny(rng,mu,si,n)
plt.figure(figsize=(10,4))
plt.subplot(1,2,1)
plt.hist(d_p,bins=range(min(d_p),max(d_p)+2),color='teal',edgecolor='black',align='left')
plt.title(f"Poisson L={la}")
plt.subplot(1,2,2)
plt.hist(d_n,bins=30,color='red',edgecolor='black')
plt.title(f"Normalny m={mu}, s={si}")
plt.tight_layout()
plt.show()