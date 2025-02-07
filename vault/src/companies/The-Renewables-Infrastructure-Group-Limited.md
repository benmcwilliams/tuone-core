```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "The-Renewables-Infrastructure-Group-Limited" or company = "The Renewables Infrastructure Group Limited")
sort location, dt_announce desc
```
