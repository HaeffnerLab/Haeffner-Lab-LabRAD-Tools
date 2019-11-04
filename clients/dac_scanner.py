import time
    
def scan_field(e,E,n):
#e is minimum field, E is maximum field, n is number of points per variable
#    d = cxn
    dEx = (E - e)/(n - 1)
    dEy = dEx
    dEz = dEx
    Ex = e - dEx
    Ey = e
    Ez = e
    fields = []

    for i in range(0,n**3):        
            if (e <= (Ex + dEx) <= E):
                Ex = Ex + dEx
            else:
                dEx = -dEx

                if (e <= (Ey + dEy) <= E):
                    Ey = Ey + dEy
                else:
                    dEy = -dEy

                    if (e <= (Ez + dEz) <= E):
                        Ez = Ez + dEz

            fields.append((Ex,Ey,Ez))
    
    return fields


    
#     for el in fields:
#         list = [('Ex',el[0]),('Ey',el[1]),('Ez',el[2]),('U3',10)]
#         d.set_multipole_values(list)
#         time.sleep(wait)
#         timer = timer - wait
#         print( timer)