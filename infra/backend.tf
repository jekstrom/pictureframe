terraform {
    backend "s3" {
    bucket = "weatherpictureframestate"
    key    = "tfstate"
    region = "us-west-2"
  }
}
