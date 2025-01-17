```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and location = "Alcalá de Guadaíra"
sort company, dt_announce desc
```
