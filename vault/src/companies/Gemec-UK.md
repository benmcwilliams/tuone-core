```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Gemec-UK" or company = "Gemec UK")
sort location, dt_announce desc
```
