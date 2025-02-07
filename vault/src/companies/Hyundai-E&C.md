```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Hyundai-E&C" or company = "Hyundai E&C")
sort location, dt_announce desc
```
