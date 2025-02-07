```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Guadalquivir-Hydrographic-Confederation" or company = "Guadalquivir Hydrographic Confederation")
sort location, dt_announce desc
```
