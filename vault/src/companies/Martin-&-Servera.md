```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Martin-&-Servera" or company = "Martin & Servera")
sort location, dt_announce desc
```
