```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Bank-of-Åland" or company = "Bank of Åland")
sort location, dt_announce desc
```
