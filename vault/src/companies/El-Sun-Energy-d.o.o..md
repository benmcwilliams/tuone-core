```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "El-Sun-Energy-d.o.o." or company = "El Sun Energy d.o.o.")
sort location, dt_announce desc
```
