```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "EDA-Renováveis,-SA" or company = "EDA Renováveis, SA")
sort location, dt_announce desc
```
