```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Netze-BW" or company = "Netze BW")
sort location, dt_announce desc
```
