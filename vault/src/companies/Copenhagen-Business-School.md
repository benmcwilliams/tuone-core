```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Copenhagen-Business-School" or company = "Copenhagen Business School")
sort location, dt_announce desc
```
