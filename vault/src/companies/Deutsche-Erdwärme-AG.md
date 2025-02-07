```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Deutsche-Erdwärme-AG" or company = "Deutsche Erdwärme AG")
sort location, dt_announce desc
```
