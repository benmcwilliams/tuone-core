```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Forss-Energy-Storage" or company = "Forss Energy Storage")
sort location, dt_announce desc
```
