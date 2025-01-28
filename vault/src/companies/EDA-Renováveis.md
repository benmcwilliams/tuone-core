```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "EDA-Renováveis" or company = "EDA Renováveis")
sort location, dt_announce desc
```
