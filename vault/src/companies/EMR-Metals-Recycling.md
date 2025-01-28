```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "EMR-Metals-Recycling" or company = "EMR Metals Recycling")
sort location, dt_announce desc
```
