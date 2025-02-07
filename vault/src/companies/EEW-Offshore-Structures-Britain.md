```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "EEW-Offshore-Structures-Britain" or company = "EEW Offshore Structures Britain")
sort location, dt_announce desc
```
