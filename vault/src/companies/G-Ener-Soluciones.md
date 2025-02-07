```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "G-Ener-Soluciones" or company = "G Ener Soluciones")
sort location, dt_announce desc
```
