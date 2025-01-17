```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and location = "Gusendos de los Oteros, Corbillos de los Oteros, Santas Martas and Pajares de los Oteros"
sort company, dt_announce desc
```
