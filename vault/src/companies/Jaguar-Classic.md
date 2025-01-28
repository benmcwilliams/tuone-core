```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Jaguar-Classic" or company = "Jaguar Classic")
sort location, dt_announce desc
```
