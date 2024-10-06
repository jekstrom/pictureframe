terraform {
    backend "s3" {
    bucket = "weatherpictureframestate"
    key    = "tfstate"
    region = "us-west-2"
  }
  required_version = ">= 1.4.4" 
}
