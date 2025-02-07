```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Solvis-d.o.o." or company = "Solvis d.o.o.")
sort location, dt_announce desc
```
