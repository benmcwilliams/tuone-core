```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Solar-Millennium-AG" or company = "Solar Millennium AG")
sort location, dt_announce desc
```
