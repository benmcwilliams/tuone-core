```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "German-solar-manufacturer" or company = "German solar manufacturer")
sort location, dt_announce desc
```
