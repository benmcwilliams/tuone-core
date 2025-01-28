```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "ZE-PAK" or company = "ZE PAK")
sort location, dt_announce desc
```
